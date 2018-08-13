/***
* Copyright (C) Microsoft. All rights reserved.
* Licensed under the MIT license. See LICENSE.txt file in the project root for full license information.
*
* =+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+
*
* HTTP Library: Client-side APIs.
*
* This file contains a cross platform implementation based on Boost.ASIO.
*
* For the latest on this and related APIs, please see: https://github.com/Microsoft/cpprestsdk
*
* =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
****/

#include "stdafx.h"

#include "cpprest/asyncrt_utils.h"
#include "../common/internal_http_helpers.h"

#if defined(__clang__)
#pragma clang diagnostic push
#pragma clang diagnostic ignored "-Wunused-local-typedef"
#pragma clang diagnostic ignored "-Winfinite-recursion"
#endif
#include <boost/asio.hpp>
#include <boost/asio/ssl.hpp>
#include <boost/asio/steady_timer.hpp>
#include <boost/algorithm/string.hpp>
#include <boost/bind.hpp>
#if defined(__clang__)
#pragma clang diagnostic pop
#endif

#if defined(BOOST_NO_CXX11_SMART_PTR)
#error "Cpp rest SDK requires c++11 smart pointer support from boost"
#endif

#include "pplx/threadpool.h"
#include "http_client_impl.h"
#include "cpprest/base_uri.h"
#include "cpprest/details/x509_cert_utilities.h"
#include "cpprest/details/http_helpers.h"
#include <unordered_set>
#include <memory>

using boost::asio::ip::tcp;

#ifdef __ANDROID__
using utility::conversions::details::to_string;
#else
using std::to_string;
#endif

#define CRLF std::string("\r\n")

namespace web { namespace http
{
namespace client
{
namespace details
{

enum class httpclient_errorcode_context
{
    none = 0,
    connect,
    handshake,
    writeheader,
    writebody,
    readheader,
    readbody,
    close
};

static std::string generate_base64_userpass(const ::web::credentials& creds)
{
    auto userpass = creds.username() + U(":") + *creds._internal_decrypt();
    auto&& u8_userpass = utility::conversions::to_utf8string(userpass);
    std::vector<unsigned char> credentials_buffer(u8_userpass.begin(), u8_userpass.end());
    return utility::conversions::to_utf8string(utility::conversions::to_base64(credentials_buffer));
}

class asio_connection_pool;

class asio_connection
{
    friend class asio_client;
public:
    asio_connection(boost::asio::io_service& io_service)
        : m_socket(io_service),
        m_is_reused(false),
        m_keep_alive(true),
        m_closed(false)
    {}

    ~asio_connection()
    {
        close();
    }

    // This simply instantiates the internal state to support ssl. It does not perform the handshake.
    void upgrade_to_ssl(const std::function<void(boost::asio::ssl::context&)>& ssl_context_callback)
    {
        std::lock_guard<std::mutex> lock(m_socket_lock);
        assert(!is_ssl());
        boost::asio::ssl::context ssl_context(boost::asio::ssl::context::sslv23);
        ssl_context.set_default_verify_paths();
        ssl_context.set_options(boost::asio::ssl::context::default_workarounds);
        if (ssl_context_callback)
        {
            ssl_context_callback(ssl_context);
        }
        m_ssl_stream = utility::details::make_unique<boost::asio::ssl::stream<boost::asio::ip::tcp::socket &>>(m_socket, ssl_context);
    }

    void close()
    {
        std::lock_guard<std::mutex> lock(m_socket_lock);

        // Ensures closed connections owned by request_context will not be put to pool when they are released.
        m_keep_alive = false;
        m_closed = true;

        boost::system::error_code error;
        m_socket.shutdown(tcp::socket::shutdown_both, error);
        m_socket.close(error);
    }

    boost::system::error_code cancel()
    {
        std::lock_guard<std::mutex> lock(m_socket_lock);
        boost::system::error_code error;
        m_socket.cancel(error);
        return error;
    }

    bool is_reused() const { return m_is_reused; }
    void set_keep_alive(bool keep_alive) { m_keep_alive = keep_alive; }
    bool keep_alive() const { return m_keep_alive; }
    bool is_ssl() const { return m_ssl_stream ? true : false; }

    template <typename Iterator, typename Handler>
    void async_connect(const Iterator &begin, const Handler &handler)
    {
        std::unique_lock<std::mutex> lock(m_socket_lock);
        if (!m_closed)
            m_socket.async_connect(begin, handler);
        else
        {
            lock.unlock();
            handler(boost::asio::error::operation_aborted);
        }
    }

    template <typename HandshakeHandler, typename CertificateHandler>
    void async_handshake(boost::asio::ssl::stream_base::handshake_type type,
                         const http_client_config &config,
                         const std::string& host_name,
                         const HandshakeHandler &handshake_handler,
                         const CertificateHandler &cert_handler)
    {
        std::lock_guard<std::mutex> lock(m_socket_lock);
        assert(is_ssl());

        // Check to turn on/off server certificate verification.
        if (config.validate_certificates())
        {
            m_ssl_stream->set_verify_mode(boost::asio::ssl::context::verify_peer);
            m_ssl_stream->set_verify_callback(cert_handler);
        }
        else
        {
            m_ssl_stream->set_verify_mode(boost::asio::ssl::context::verify_none);
        }

        // Check to set host name for Server Name Indication (SNI)
        if (config.is_tlsext_sni_enabled())
        {
            SSL_set_tlsext_host_name(m_ssl_stream->native_handle(), const_cast<char *>(host_name.data()));
        }

        m_ssl_stream->async_handshake(type, handshake_handler);
    }

    template <typename ConstBufferSequence, typename Handler>
    void async_write(ConstBufferSequence &buffer, const Handler &writeHandler)
    {
        std::lock_guard<std::mutex> lock(m_socket_lock);
        if (m_ssl_stream)
        {
            boost::asio::async_write(*m_ssl_stream, buffer, writeHandler);
        }
        else
        {
            boost::asio::async_write(m_socket, buffer, writeHandler);
        }
    }

    template <typename MutableBufferSequence, typename CompletionCondition, typename Handler>
    void async_read(MutableBufferSequence &buffer, const CompletionCondition &condition, const Handler &readHandler)
    {
        std::lock_guard<std::mutex> lock(m_socket_lock);
        if (m_ssl_stream)
        {
            boost::asio::async_read(*m_ssl_stream, buffer, condition, readHandler);
        }
        else
        {
            boost::asio::async_read(m_socket, buffer, condition, readHandler);
        }
    }

    template <typename Handler>
    void async_read_until(boost::asio::streambuf &buffer, const std::string &delim, const Handler &readHandler)
    {
        std::lock_guard<std::mutex> lock(m_socket_lock);
        if (m_ssl_stream)
        {
            boost::asio::async_read_until(*m_ssl_stream, buffer, delim, readHandler);
        }
        else
        {
            boost::asio::async_read_until(m_socket, buffer, delim, readHandler);
        }
    }

    void start_reuse()
    {
        m_is_reused = true;
    }

private:
    // Guards concurrent access to socket/ssl::stream. This is necessary
    // because timeouts and cancellation can touch the socket at the same time
    // as normal message processing.
    std::mutex m_socket_lock;
    tcp::socket m_socket;
    std::unique_ptr<boost::asio::ssl::stream<tcp::socket &> > m_ssl_stream;

    bool m_is_reused;
    bool m_keep_alive;
    bool m_closed;
};

/// <summary>Implements a connection pool with adaptive connection removal</summary>
/// <remarks>
/// The timeout mechanism is based on the `uint64_t m_epoch` member. Every 30 seconds,
/// the lambda in `start_epoch_interval` fires, triggering the cleanup of any
/// connections that have resided in the pool since the last cleanup phase's epoch.
///
/// This works because the `m_connections` member functions is used in LIFO order.
/// LIFO usage guarantees that the elements remain sorted based on epoch number,
/// since the highest epoch is always removed and on insertion the next monotonically
/// increasing epoch is used.
///
/// During the cleanup phase, connections are removed starting with the oldest. This
/// ensures that if a high intensity workload is followed by a low intensity workload,
/// the connection pool will correctly adapt to the low intensity workload.
///
/// Specifically, the following code will eventually result in a maximum of one pooled
/// connection regardless of the initial number of pooled connections:
/// <code>
///   while(1)
///   {
///     auto conn = pool.acquire();
///     if (!conn) conn = new_conn();
///     pool.release(conn);
///   }
/// </code>
/// </remarks>
class asio_connection_pool : public std::enable_shared_from_this<asio_connection_pool>
{
public:
    asio_connection_pool() : m_pool_epoch_timer(crossplat::threadpool::shared_instance().service())
    {}

    std::shared_ptr<asio_connection> acquire()
    {
        std::lock_guard<std::mutex> lock(m_lock);

        if (m_connections.empty())
            return nullptr;

        auto conn = std::move(m_connections.back().second);
        m_connections.pop_back();
        conn->start_reuse();
        return conn;
    }

    void release(const std::shared_ptr<asio_connection>& connection)
    {
        connection->cancel();

        if (!connection->keep_alive())
            return;

        std::lock_guard<std::mutex> lock(m_lock);
        if (!is_timer_running)
        {
            start_epoch_interval(shared_from_this());
            is_timer_running = true;
        }

        m_epoch++;
        m_connections.emplace_back(m_epoch, std::move(connection));
    }

private:
    // Note: must be called under m_lock
    static void start_epoch_interval(const std::shared_ptr<asio_connection_pool>& pool)
    {
        _ASSERTE(pool.get() != nullptr);

        auto& self = *pool;
        std::weak_ptr<asio_connection_pool> weak_pool = pool;

        self.m_prev_epoch = self.m_epoch;
        pool->m_pool_epoch_timer.expires_from_now(boost::posix_time::seconds(30));
        pool->m_pool_epoch_timer.async_wait([weak_pool](const boost::system::error_code& ec)
        {
            if (ec)
                return;

            auto pool = weak_pool.lock();
            if (!pool)
                return;
            auto& self = *pool;

            std::lock_guard<std::mutex> lock(self.m_lock);
            if (self.m_prev_epoch == self.m_epoch)
            {
                self.m_connections.clear();
                self.is_timer_running = false;
                return;
            }
            else
            {
                auto prev_epoch = self.m_prev_epoch;
                auto erase_end = std::find_if(self.m_connections.begin(), self.m_connections.end(),
                    [prev_epoch](std::pair<uint64_t, std::shared_ptr<asio_connection>>& p)
                {
                    return p.first > prev_epoch;
                });

                self.m_connections.erase(self.m_connections.begin(), erase_end);
                start_epoch_interval(pool);
            }
        });
    }

    std::mutex m_lock;
    std::deque<std::pair<uint64_t, std::shared_ptr<asio_connection>>> m_connections;

    uint64_t m_epoch = 0;
    uint64_t m_prev_epoch = 0;
    bool is_timer_running = false;
    boost::asio::deadline_timer m_pool_epoch_timer;
};

class asio_client final : public _http_client_communicator
{
public:
    asio_client(http::uri&& address, http_client_config&& client_config)
        : _http_client_communicator(std::move(address), std::move(client_config))
        , m_resolver(crossplat::threadpool::shared_instance().service())
        , m_pool(std::make_shared<asio_connection_pool>())
        , m_start_with_ssl(base_uri().scheme() == U("https") && !this->client_config().proxy().is_specified())
    {}

    void send_request(const std::shared_ptr<request_context> &request_ctx) override;

    unsigned long open() override { return 0; }

    void release_connection(std::shared_ptr<asio_connection>& conn)
    {
        m_pool->release(conn);
    }
    std::shared_ptr<asio_connection> obtain_connection()
    {
        std::shared_ptr<asio_connection> conn = m_pool->acquire();

        if (conn == nullptr)
        {
            // Pool was empty. Create a new connection
            conn = std::make_shared<asio_connection>(crossplat::threadpool::shared_instance().service());
            if (m_start_with_ssl)
                conn->upgrade_to_ssl(this->client_config().get_ssl_context_callback());
        }

        return conn;
    }

    virtual pplx::task<http_response> propagate(http_request request) override;

public:
    tcp::resolver m_resolver;
private:
    const std::shared_ptr<asio_connection_pool> m_pool;
    const bool m_start_with_ssl;
};

class asio_context : public request_context, public std::enable_shared_from_this<asio_context>
{
    friend class asio_client;
public:
    asio_context(const std::shared_ptr<_http_client_communicator> &client,
                 http_request &request,
                 const std::shared_ptr<asio_connection> &connection)
    : request_context(client, request)
    , m_content_length(0)
    , m_needChunked(false)
    , m_timer(client->client_config().timeout<std::chrono::microseconds>())
    , m_connection(connection)
#if defined(__APPLE__) || (defined(ANDROID) || defined(__ANDROID__))
    , m_openssl_failed(false)
#endif
    {}

    virtual ~asio_context()
    {
        m_timer.stop();
        // Release connection back to the pool. If connection was not closed, it will be put to the pool for reuse.
        std::static_pointer_cast<asio_client>(m_http_client)->release_connection(m_connection);
    }

    static std::shared_ptr<request_context> create_request_context(std::shared_ptr<_http_client_communicator> &client, http_request &request)
    {
        auto client_cast(std::static_pointer_cast<asio_client>(client));
        auto connection(client_cast->obtain_connection());
        auto ctx = std::make_shared<asio_context>(client, request, connection);
        ctx->m_timer.set_ctx(std::weak_ptr<asio_context>(ctx));
        return ctx;
    }
    
    class ssl_proxy_tunnel : public std::enable_shared_from_this<ssl_proxy_tunnel>
    {
    public:
        ssl_proxy_tunnel(std::shared_ptr<asio_context> context, std::function<void(std::shared_ptr<asio_context>)> ssl_tunnel_established)
            : m_ssl_tunnel_established(ssl_tunnel_established), m_context(context)
        {}
        
        void start_proxy_connect()
        {
            auto proxy = m_context->m_http_client->client_config().proxy();
            auto proxy_uri = proxy.address();

            utility::string_t proxy_host = proxy_uri.host();
            int proxy_port = proxy_uri.port() == -1 ? 8080 : proxy_uri.port();

            const auto &base_uri = m_context->m_http_client->base_uri();
            const auto &host = utility::conversions::to_utf8string(base_uri.host());

            std::ostream request_stream(&m_request);
            request_stream.imbue(std::locale::classic());

            request_stream << "CONNECT " << host << ":" << 443 << " HTTP/1.1" << CRLF;
            request_stream << "Host: " << host << ":" << 443 << CRLF;
            request_stream << "Proxy-Connection: Keep-Alive" << CRLF;

            if(m_context->m_http_client->client_config().proxy().credentials().is_set())
            {
                request_stream << m_context->generate_basic_proxy_auth_header() << CRLF;
            }

            request_stream << CRLF;

            m_context->m_timer.start();

            tcp::resolver::query query(utility::conversions::to_utf8string(proxy_host), to_string(proxy_port));

            auto client = std::static_pointer_cast<asio_client>(m_context->m_http_client);
            client->m_resolver.async_resolve(query, boost::bind(&ssl_proxy_tunnel::handle_resolve, shared_from_this(), boost::asio::placeholders::error, boost::asio::placeholders::iterator));
        }

    private: 
        void handle_resolve(const boost::system::error_code& ec, tcp::resolver::iterator endpoints)
        {
            if (ec)
            {
                m_context->report_error("Error resolving proxy address", ec, httpclient_errorcode_context::connect);
            }
            else
            {
                m_context->m_timer.reset();
                auto endpoint = *endpoints;
                m_context->m_connection->async_connect(endpoint, boost::bind(&ssl_proxy_tunnel::handle_tcp_connect, shared_from_this(), boost::asio::placeholders::error, ++endpoints));
            }
        }

        void handle_tcp_connect(const boost::system::error_code& ec, tcp::resolver::iterator endpoints)
        {
            if (!ec)
            {
                m_context->m_timer.reset();
                m_context->m_connection->async_write(m_request, boost::bind(&ssl_proxy_tunnel::handle_write_request, shared_from_this(), boost::asio::placeholders::error));
            }
            else if (endpoints == tcp::resolver::iterator())
            {
                m_context->report_error("Failed to connect to any resolved proxy endpoint", ec, httpclient_errorcode_context::connect);
            }
            else
            {
                m_context->m_timer.reset();
                //// Replace the connection. This causes old connection object to go out of scope.
                auto client = std::static_pointer_cast<asio_client>(m_context->m_http_client);
                m_context->m_connection = client->obtain_connection();

                auto endpoint = *endpoints;
                m_context->m_connection->async_connect(endpoint, boost::bind(&ssl_proxy_tunnel::handle_tcp_connect, shared_from_this(), boost::asio::placeholders::error, ++endpoints));
            }

        }

        void handle_write_request(const boost::system::error_code& err)
        {
            if (!err)
            {
                m_context->m_timer.reset();
                m_context->m_connection->async_read_until(m_response, CRLF + CRLF, boost::bind(&ssl_proxy_tunnel::handle_status_line, shared_from_this(), boost::asio::placeholders::error));
            }
            else
            {
                m_context->report_error("Failed to send connect request to proxy.", err, httpclient_errorcode_context::writebody);
            }
        }
    
        void handle_status_line(const boost::system::error_code& ec)
        {
            if (!ec)
            {
                m_context->m_timer.reset();
                std::istream response_stream(&m_response);
                response_stream.imbue(std::locale::classic());
                std::string http_version;
                response_stream >> http_version;
                status_code status_code;
                response_stream >> status_code;
                
                if (!response_stream || http_version.substr(0, 5) != "HTTP/")
                {
                    m_context->report_error("Invalid HTTP status line during proxy connection", ec, httpclient_errorcode_context::readheader);
                    return;
                }
                
                if (status_code != 200)
                {
                    m_context->report_error("Expected a 200 response from proxy, received: " + to_string(status_code), ec, httpclient_errorcode_context::readheader);
                    return;
                }

                m_context->m_connection->upgrade_to_ssl(m_context->m_http_client->client_config().get_ssl_context_callback());

                m_ssl_tunnel_established(m_context);
            }
            else
            {
                // These errors tell if connection was closed.
                const bool socket_was_closed((boost::asio::error::eof == ec)
                    || (boost::asio::error::connection_reset == ec)
                    || (boost::asio::error::connection_aborted == ec));
                if (socket_was_closed && m_context->m_connection->is_reused())
                {
                    // Failed to write to socket because connection was already closed while it was in the pool.
                    // close() here ensures socket is closed in a robust way and prevents the connection from being put to the pool again.
                    m_context->m_connection->close();
            
                    // Create a new context and copy the request object, completion event and
                    // cancellation registration to maintain the old state.
                    // This also obtains a new connection from pool.
                    auto new_ctx = m_context->create_request_context(m_context->m_http_client, m_context->m_request);
                    new_ctx->m_request_completion = m_context->m_request_completion;
                    new_ctx->m_cancellationRegistration = m_context->m_cancellationRegistration;
            
                    auto client = std::static_pointer_cast<asio_client>(m_context->m_http_client);
                    // Resend the request using the new context.
                    client->send_request(new_ctx);
                }
                else
                {
                    m_context->report_error("Failed to read HTTP status line from proxy", ec, httpclient_errorcode_context::readheader);
                }
            }
        }
    
        std::function<void(std::shared_ptr<asio_context>)> m_ssl_tunnel_established;
        std::shared_ptr<asio_context> m_context;
    
        boost::asio::streambuf m_request;
        boost::asio::streambuf m_response;
    };
    
    
    enum class http_proxy_type
    {
        none,
        http,
        ssl_tunnel
    };

    void start_request()
    {
        if (m_request._cancellation_token().is_canceled())
        {
            request_context::report_error(make_error_code(std::errc::operation_canceled).value(), "Request canceled by user.");
            return;
        }
        
        http_proxy_type proxy_type = http_proxy_type::none;
        std::string proxy_host;
        int proxy_port = -1;
        
        // There is no support for auto-detection of proxies on non-windows platforms, it must be specified explicitly from the client code.
        if (m_http_client->client_config().proxy().is_specified())
        {
            proxy_type = m_http_client->base_uri().scheme() == U("https") ? http_proxy_type::ssl_tunnel : http_proxy_type::http;
            auto proxy = m_http_client->client_config().proxy();
            auto proxy_uri = proxy.address();
            proxy_port = proxy_uri.port() == -1 ? 8080 : proxy_uri.port();
            proxy_host = utility::conversions::to_utf8string(proxy_uri.host());
        }
        
        auto start_http_request_flow = [proxy_type, proxy_host, proxy_port](std::shared_ptr<asio_context> ctx)
        {
            if (ctx->m_request._cancellation_token().is_canceled())
            {
                ctx->request_context::report_error(make_error_code(std::errc::operation_canceled).value(), "Request canceled by user.");
                return;
            }
                
            const auto &base_uri = ctx->m_http_client->base_uri();
            const auto full_uri = uri_builder(base_uri).append(ctx->m_request.relative_uri()).to_uri();
                
            // For a normal http proxy, we need to specify the full request uri, otherwise just specify the resource
            auto encoded_resource = proxy_type == http_proxy_type::http ? full_uri.to_string() : full_uri.resource().to_string();
                
            if (encoded_resource.empty())
            {
                encoded_resource = U("/");
            }
                
            const auto &method = ctx->m_request.method();
                
            // stop injection of headers via method
            // resource should be ok, since it's been encoded
            // and host won't resolve
            if (!::web::http::details::validate_method(method))
            {
                ctx->report_exception(http_exception("The method string is invalid."));
                return;
            }
                
            std::ostream request_stream(&ctx->m_body_buf);
            request_stream.imbue(std::locale::classic());
            const auto &host = utility::conversions::to_utf8string(base_uri.host());
                
            request_stream << utility::conversions::to_utf8string(method) << " " << utility::conversions::to_utf8string(encoded_resource) << " " << "HTTP/1.1" << CRLF;
                
            int port = base_uri.port();
                
            if (base_uri.is_port_default())
            {
                port = (ctx->m_connection->is_ssl() ? 443 : 80);
            }
                
            // Add the Host header if user has not specified it explicitly
            if (!ctx->m_request.headers().has(header_names::host))
            {
                request_stream << "Host: " << host;
                if (!base_uri.is_port_default()) {
                    request_stream << ":" << port;
                }
                request_stream << CRLF;
            }
                
            // Extra request headers are constructed here.
            std::string extra_headers;
                
            // Add header for basic proxy authentication
            if (proxy_type == http_proxy_type::http && ctx->m_http_client->client_config().proxy().credentials().is_set())
            {
                extra_headers.append(ctx->generate_basic_proxy_auth_header());
            }

            if (ctx->m_http_client->client_config().credentials().is_set())
            {
                extra_headers.append(ctx->generate_basic_auth_header());
            }

            // Add the header needed to request a compressed response if supported on this platform and it has been specified in the config
            if (web::http::details::compression::stream_decompressor::is_supported() && ctx->m_http_client->client_config().request_compressed_response())
            {
                extra_headers.append("Accept-Encoding: deflate, gzip\r\n");
            }

            // Check user specified transfer-encoding.
            std::string transferencoding;
            if (ctx->m_request.headers().match(header_names::transfer_encoding, transferencoding) && transferencoding == "chunked")
            {
                ctx->m_needChunked = true;
            }
            else if (!ctx->m_request.headers().match(header_names::content_length, ctx->m_content_length))
            {
                // Stream without content length is the signal of requiring transfer encoding chunked.
                if (ctx->m_request.body())
                {
                    ctx->m_needChunked = true;
                    extra_headers.append("Transfer-Encoding:chunked\r\n");
                }
                else if (ctx->m_request.method() == methods::POST || ctx->m_request.method() == methods::PUT)
                {
                    // Some servers do not accept POST/PUT requests with a content length of 0, such as
                    // lighttpd - http://serverfault.com/questions/315849/curl-post-411-length-required
                    // old apache versions - https://issues.apache.org/jira/browse/TS-2902
                    extra_headers.append("Content-Length: 0\r\n");
                }
            }
                
            if (proxy_type == http_proxy_type::http)
            {
                extra_headers.append(
                    "Cache-Control: no-store, no-cache\r\n"
                    "Pragma: no-cache\r\n");
            }
                
            request_stream << utility::conversions::to_utf8string(::web::http::details::flatten_http_headers(ctx->m_request.headers()));
            request_stream << extra_headers;
            // Enforce HTTP connection keep alive (even for the old HTTP/1.0 protocol).
            request_stream << "Connection: Keep-Alive" << CRLF << CRLF;
                
            // Start connection timeout timer.
            if (!ctx->m_timer.has_started())
            {
                ctx->m_timer.start();
            }
                
            if (ctx->m_connection->is_reused() || proxy_type == http_proxy_type::ssl_tunnel)
            {
                // If socket is a reused connection or we're connected via an ssl-tunneling proxy, try to write the request directly. In both cases we have already established a tcp connection.
                ctx->write_request();
            }
            else
            {
                // If the connection is new (unresolved and unconnected socket), then start async
                // call to resolve first, leading eventually to request write.
                    
                // For normal http proxies, we want to connect directly to the proxy server. It will relay our request.
                auto tcp_host = proxy_type == http_proxy_type::http ? proxy_host : host;
                auto tcp_port = proxy_type == http_proxy_type::http ? proxy_port : port;
                    
                tcp::resolver::query query(tcp_host, to_string(tcp_port));
                auto client = std::static_pointer_cast<asio_client>(ctx->m_http_client);
                client->m_resolver.async_resolve(query, boost::bind(&asio_context::handle_resolve, ctx, boost::asio::placeholders::error, boost::asio::placeholders::iterator));
            }
        
                // Register for notification on cancellation to abort this request.
            if (ctx->m_request._cancellation_token() != pplx::cancellation_token::none())
            {
                // weak_ptr prevents lambda from taking shared ownership of the context.
                // Otherwise context replacement in the handle_status_line() would leak the objects.
                std::weak_ptr<asio_context> ctx_weak(ctx);
                ctx->m_cancellationRegistration = ctx->m_request._cancellation_token().register_callback([ctx_weak]()
                {
                    if (auto ctx_lock = ctx_weak.lock())
                    {
                        // Shut down transmissions, close the socket and prevent connection from being pooled.
                        ctx_lock->m_connection->close();
                    }
                });
            }
        };
        
        if (proxy_type == http_proxy_type::ssl_tunnel)
        {
            // The ssl_tunnel_proxy keeps the context alive and then calls back once the ssl tunnel is established via 'start_http_request_flow'
            std::shared_ptr<ssl_proxy_tunnel> ssl_tunnel = std::make_shared<ssl_proxy_tunnel>(shared_from_this(), start_http_request_flow);
            ssl_tunnel->start_proxy_connect();
        }
        else
        {
            start_http_request_flow(shared_from_this());
        }
    }

    template<typename _ExceptionType>
    void report_exception(const _ExceptionType &e)
    {
        report_exception(std::make_exception_ptr(e));
    }

    void report_exception(std::exception_ptr exceptionPtr) override
    {
        // Don't recycle connections that had an error into the connection pool.
        m_connection->close();
        request_context::report_exception(exceptionPtr);
    }

private:
    std::string generate_basic_auth_header()
    {
        std::string header;
        header.append("Authorization: Basic ");
        header.append(generate_base64_userpass(m_http_client->client_config().credentials()));
        header.append(CRLF);
        return header;
    }

    std::string generate_basic_proxy_auth_header()
    {
        std::string header;
        header.append("Proxy-Authorization: Basic ");
        header.append(generate_base64_userpass(m_http_client->client_config().proxy().credentials()));
        header.append(CRLF);
        return header;
    }

    void report_error(const std::string &message, const boost::system::error_code &ec, httpclient_errorcode_context context = httpclient_errorcode_context::none)
    {
        // By default, errorcodeValue don't need to converted
        long errorcodeValue = ec.value();

        // map timer cancellation to time_out
        if (m_timer.has_timedout())
        {
            errorcodeValue = make_error_code(std::errc::timed_out).value();
        }
        else
        {
            // We need to correct inaccurate ASIO error code base on context information
            switch (context)
            {
                case httpclient_errorcode_context::writeheader:
                    if (ec == boost::system::errc::broken_pipe)
                    {
                        errorcodeValue = make_error_code(std::errc::host_unreachable).value();
                    }
                    break;
                case httpclient_errorcode_context::connect:
                    if (ec == boost::system::errc::connection_refused)
                    {
                        errorcodeValue = make_error_code(std::errc::host_unreachable).value();
                    }
                    break;
                case httpclient_errorcode_context::readheader:
                    if (ec.default_error_condition().value() == boost::system::errc::no_such_file_or_directory) // bug in boost error_code mapping
                    {
                        errorcodeValue = make_error_code(std::errc::connection_aborted).value();
                    }
                    break;
                default:
                    break;
            }
        }
        request_context::report_error(errorcodeValue, message);
    }

    void handle_connect(const boost::system::error_code& ec, tcp::resolver::iterator endpoints)
    {
        m_timer.reset();
        if (!ec)
        {
            write_request();
        }
        else if (ec.value() == boost::system::errc::operation_canceled || ec.value() == boost::asio::error::operation_aborted)
        {
            request_context::report_error(ec.value(), "Request canceled by user.");
        }
        else if (endpoints == tcp::resolver::iterator())
        {
            report_error("Failed to connect to any resolved endpoint", ec, httpclient_errorcode_context::connect);
        }
        else
        {
            // Replace the connection. This causes old connection object to go out of scope.
            auto client = std::static_pointer_cast<asio_client>(m_http_client);
            m_connection = client->obtain_connection();

            auto endpoint = *endpoints;
            m_connection->async_connect(endpoint, boost::bind(&asio_context::handle_connect, shared_from_this(), boost::asio::placeholders::error, ++endpoints));
        }
    }

    void handle_resolve(const boost::system::error_code& ec, tcp::resolver::iterator endpoints)
    {
        if (ec)
        {
            report_error("Error resolving address", ec, httpclient_errorcode_context::connect);
        }
        else
        {
            m_timer.reset();
            auto endpoint = *endpoints;
            m_connection->async_connect(endpoint, boost::bind(&asio_context::handle_connect, shared_from_this(), boost::asio::placeholders::error, ++endpoints));
        }
    }

    void write_request()
    {
        // Only perform handshake if a TLS connection and not being reused.
        if (m_connection->is_ssl() && !m_connection->is_reused())
        {
            const auto weakCtx = std::weak_ptr<asio_context>(shared_from_this());
            m_connection->async_handshake(boost::asio::ssl::stream_base::client,
                                          m_http_client->client_config(),
                                          utility::conversions::to_utf8string(m_http_client->base_uri().host()),
                                          boost::bind(&asio_context::handle_handshake, shared_from_this(), boost::asio::placeholders::error),

                                          // Use a weak_ptr since the verify_callback is stored until the connection is destroyed.
                                          // This avoids creating a circular reference since we pool connection objects.
                                          [weakCtx](bool preverified, boost::asio::ssl::verify_context &verify_context)
                                          {
                                              auto this_request = weakCtx.lock();
                                              if(this_request)
                                              {
                                                  return this_request->handle_cert_verification(preverified, verify_context);
                                              }
                                              return false;
                                          });
        }
        else
        {
            m_connection->async_write(m_body_buf, boost::bind(&asio_context::handle_write_headers, shared_from_this(), boost::asio::placeholders::error));
        }
    }

    void handle_handshake(const boost::system::error_code& ec)
    {
        if (!ec)
        {
            m_connection->async_write(m_body_buf, boost::bind(&asio_context::handle_write_headers, shared_from_this(), boost::asio::placeholders::error));
        }
        else
        {
            report_error("Error in SSL handshake", ec, httpclient_errorcode_context::handshake);
        }
    }

    bool handle_cert_verification(bool preverified, boost::asio::ssl::verify_context &verifyCtx)
    {
        // OpenSSL calls the verification callback once per certificate in the chain,
        // starting with the root CA certificate. The 'leaf', non-Certificate Authority (CA)
        // certificate, i.e. actual server certificate is at the '0' position in the
        // certificate chain, the rest are optional intermediate certificates, followed
        // finally by the root CA self signed certificate.

        const auto &host = utility::conversions::to_utf8string(m_http_client->base_uri().host());
#if defined(__APPLE__) || (defined(ANDROID) || defined(__ANDROID__))
        // On OS X, iOS, and Android, OpenSSL doesn't have access to where the OS
        // stores keychains. If OpenSSL fails we will doing verification at the
        // end using the whole certificate chain so wait until the 'leaf' cert.
        // For now return true so OpenSSL continues down the certificate chain.
        if(!preverified)
        {
            m_openssl_failed = true;
        }
        if(m_openssl_failed)
        {
            return verify_cert_chain_platform_specific(verifyCtx, host);
        }
#endif

        boost::asio::ssl::rfc2818_verification rfc2818(host);
        return rfc2818(preverified, verifyCtx);
    }

    void handle_write_headers(const boost::system::error_code& ec)
    {
        if(ec)
        {
            report_error("Failed to write request headers", ec, httpclient_errorcode_context::writeheader);
        }
        else
        {
            if (m_needChunked)
            {
                handle_write_chunked_body(ec);
            }
            else
            {
                handle_write_large_body(ec);
            }
        }
    }


    void handle_write_chunked_body(const boost::system::error_code& ec)
    {
        if (ec)
        {
            // Reuse error handling.
            return handle_write_body(ec);
        }

        m_timer.reset();
        const auto &progress = m_request._get_impl()->_progress_handler();
        if (progress)
        {
            try
            {
                (*progress)(message_direction::upload, m_uploaded);
            }
            catch(...)
            {
                report_exception(std::current_exception());
                return;
            }
        }

        const auto & chunkSize = m_http_client->client_config().chunksize();
        auto readbuf = _get_readbuffer();
        uint8_t *buf = boost::asio::buffer_cast<uint8_t *>(m_body_buf.prepare(chunkSize + http::details::chunked_encoding::additional_encoding_space));
        const auto this_request = shared_from_this();
        readbuf.getn(buf + http::details::chunked_encoding::data_offset, chunkSize).then([this_request, buf, chunkSize](pplx::task<size_t> op)
        {
            size_t readSize = 0;
            try
            {
                readSize = op.get();
            }
            catch (...)
            {
                this_request->report_exception(std::current_exception());
                return;
            }

            const size_t offset = http::details::chunked_encoding::add_chunked_delimiters(buf, chunkSize + http::details::chunked_encoding::additional_encoding_space, readSize);
            this_request->m_body_buf.commit(readSize + http::details::chunked_encoding::additional_encoding_space);
            this_request->m_body_buf.consume(offset);
            this_request->m_uploaded += static_cast<uint64_t>(readSize);

            if (readSize != 0)
            {
                this_request->m_connection->async_write(this_request->m_body_buf,
                                                        boost::bind(&asio_context::handle_write_chunked_body, this_request, boost::asio::placeholders::error));
            }
            else
            {
                this_request->m_connection->async_write(this_request->m_body_buf,
                                                        boost::bind(&asio_context::handle_write_body, this_request, boost::asio::placeholders::error));
            }
        });
    }

    void handle_write_large_body(const boost::system::error_code& ec)
    {
        if (ec || m_uploaded >= m_content_length)
        {
            // Reuse error handling.
            return handle_write_body(ec);
        }
        
        m_timer.reset();
        const auto &progress = m_request._get_impl()->_progress_handler();
        if (progress)
        {
            try
            {
                (*progress)(message_direction::upload, m_uploaded);
            }
            catch(...)
            {
                report_exception(std::current_exception());
                return;
            }
        }

        const auto this_request = shared_from_this();
        const auto readSize = static_cast<size_t>(std::min(static_cast<uint64_t>(m_http_client->client_config().chunksize()), m_content_length - m_uploaded));
        auto readbuf = _get_readbuffer();
        readbuf.getn(boost::asio::buffer_cast<uint8_t *>(m_body_buf.prepare(readSize)), readSize).then([this_request](pplx::task<size_t> op)
        {
            try
            {
                const auto actualReadSize = op.get();
                if(actualReadSize == 0)
                {
                    this_request->report_exception(http_exception("Unexpected end of request body stream encountered before Content-Length satisfied."));
                    return;
                }
                this_request->m_uploaded += static_cast<uint64_t>(actualReadSize);
                this_request->m_body_buf.commit(actualReadSize);
                this_request->m_connection->async_write(this_request->m_body_buf, boost::bind(&asio_context::handle_write_large_body, this_request, boost::asio::placeholders::error));
            }
            catch (...)
            {
                this_request->report_exception(std::current_exception());
                return;
            }
        });
    }

    void handle_write_body(const boost::system::error_code& ec)
    {
        if (!ec)
        {
            m_timer.reset();
            const auto &progress = m_request._get_impl()->_progress_handler();
            if (progress)
            {
                try
                {
                    (*progress)(message_direction::upload, m_uploaded);
                }
                catch(...)
                {
                    report_exception(std::current_exception());
                    return;
                }
            }

            // Read until the end of entire headers
            m_connection->async_read_until(m_body_buf, CRLF + CRLF, boost::bind(&asio_context::handle_status_line, shared_from_this(), boost::asio::placeholders::error));
        }
        else
        {
            report_error("Failed to write request body", ec, httpclient_errorcode_context::writebody);
        }
    }

    void handle_status_line(const boost::system::error_code& ec)
    {
        if (!ec)
        {
            m_timer.reset();

            std::istream response_stream(&m_body_buf);
            response_stream.imbue(std::locale::classic());
            std::string http_version;
            response_stream >> http_version;
            status_code status_code;
            response_stream >> status_code;
            
            std::string status_message;
            std::getline(response_stream, status_message);

            m_response.set_status_code(status_code);

            ::web::http::details::trim_whitespace(status_message);
            m_response.set_reason_phrase(utility::conversions::to_string_t(std::move(status_message)));

            if (!response_stream || http_version.substr(0, 5) != "HTTP/")
            {
                report_error("Invalid HTTP status line", ec, httpclient_errorcode_context::readheader);
                return;
            }

            read_headers();
        }
        else
        {
            // These errors tell if connection was closed.
            const bool socket_was_closed((boost::asio::error::eof == ec)
                                         || (boost::asio::error::connection_reset == ec)
                                         || (boost::asio::error::connection_aborted == ec));
            if (socket_was_closed && m_connection->is_reused())
            {
                // Failed to write to socket because connection was already closed while it was in the pool.
                // close() here ensures socket is closed in a robust way and prevents the connection from being put to the pool again.
                m_connection->close();

                // Create a new context and copy the request object, completion event and
                // cancellation registration to maintain the old state.
                // This also obtains a new connection from pool.
                auto new_ctx = create_request_context(m_http_client, m_request);
                new_ctx->m_request_completion = m_request_completion;
                new_ctx->m_cancellationRegistration = m_cancellationRegistration;

                auto client = std::static_pointer_cast<asio_client>(m_http_client);
                // Resend the request using the new context.
                client->send_request(new_ctx);
            }
            else
            {
                report_error("Failed to read HTTP status line", ec, httpclient_errorcode_context::readheader);
            }
        }
    }

    void read_headers()
    {
        auto needChunked = false;
        std::istream response_stream(&m_body_buf);
        response_stream.imbue(std::locale::classic());
        std::string header;
        while (std::getline(response_stream, header) && header != "\r")
        {
            const auto colon = header.find(':');
            if (colon != std::string::npos)
            {
                auto name = header.substr(0, colon);
                auto value = header.substr(colon + 1, header.size() - colon - 2);
                boost::algorithm::trim(name);
                boost::algorithm::trim(value);

                if (boost::iequals(name, header_names::transfer_encoding))
                {
                    needChunked = boost::iequals(value, U("chunked"));
                }

                if (boost::iequals(name, header_names::connection))
                {
                    // This assumes server uses HTTP/1.1 so that 'Keep-Alive' is the default,
                    // so connection is explicitly closed only if we get "Connection: close".
                    // We don't handle HTTP/1.0 server here. HTTP/1.0 server would need
                    // to respond using 'Connection: Keep-Alive' every time.
                    m_connection->set_keep_alive(!boost::iequals(value, U("close")));
                }

                m_response.headers().add(utility::conversions::to_string_t(std::move(name)), utility::conversions::to_string_t(std::move(value)));
            }
        }
        complete_headers();

        m_content_length = std::numeric_limits<size_t>::max(); // Without Content-Length header, size should be same as TCP stream - set it size_t max.
        m_response.headers().match(header_names::content_length, m_content_length);

        utility::string_t content_encoding;
        if(web::http::details::compression::stream_decompressor::is_supported() && m_response.headers().match(header_names::content_encoding, content_encoding))
        {
            auto alg = web::http::details::compression::stream_decompressor::to_compression_algorithm(content_encoding);

            if (alg != web::http::details::compression::compression_algorithm::invalid)
            {
                m_decompressor = utility::details::make_unique<web::http::details::compression::stream_decompressor>(alg);
            }
            else
            {
                report_exception(std::runtime_error("Unsupported compression algorithm in the Content Encoding header: " + utility::conversions::to_utf8string(content_encoding)));
            }
        }

        // Check for HEAD requests and status codes which cannot contain a
        // message body in HTTP/1.1 (see 3.3.3/1 of the RFC 7230).
        //
        // note: need to check for 'chunked' here as well, azure storage sends both
        // transfer-encoding:chunked and content-length:0 (although HTTP says not to)
        const auto status = m_response.status_code();
        if (m_request.method() == U("HEAD")
            || (status >= 100 && status < 200)
            || status == status_codes::NoContent
            || status == status_codes::NotModified
            || (!needChunked && m_content_length == 0))
        {
            // we can stop early - no body
            const auto &progress = m_request._get_impl()->_progress_handler();
            if (progress)
            {
                try
                {
                    (*progress)(message_direction::download, 0);
                }
                catch(...)
                {
                    report_exception(std::current_exception());
                    return;
                }
            }

            complete_request(0);
        }
        else
        {
            if (!needChunked)
            {
                async_read_until_buffersize(static_cast<size_t>(std::min(m_content_length, static_cast<uint64_t>(m_http_client->client_config().chunksize()))),
                                            boost::bind(&asio_context::handle_read_content, shared_from_this(), boost::asio::placeholders::error));
            }
            else
            {
                m_connection->async_read_until(m_body_buf, CRLF, boost::bind(&asio_context::handle_chunk_header, shared_from_this(), boost::asio::placeholders::error));
            }
        }
    }

    template <typename ReadHandler>
    void async_read_until_buffersize(size_t size, const ReadHandler &handler)
    {
        size_t size_to_read = 0;
        if (m_body_buf.size() < size)
        {
            size_to_read = size - m_body_buf.size();
        }

        m_connection->async_read(m_body_buf, boost::asio::transfer_exactly(size_to_read), handler);
    }

    void handle_chunk_header(const boost::system::error_code& ec)
    {
        if (!ec)
        {
            m_timer.reset();

            std::istream response_stream(&m_body_buf);
            response_stream.imbue(std::locale::classic());
            std::string line;
            std::getline(response_stream, line);

            std::istringstream octetLine(std::move(line));
            octetLine.imbue(std::locale::classic());
            int octets = 0;
            octetLine >> std::hex >> octets;

            if (octetLine.fail())
            {
                report_error("Invalid chunked response header", boost::system::error_code(), httpclient_errorcode_context::readbody);
            }
            else
            {
                async_read_until_buffersize(octets + CRLF.size(), // + 2 for crlf
                                            boost::bind(&asio_context::handle_chunk, shared_from_this(), boost::asio::placeholders::error, octets));
            }
        }
        else
        {
            report_error("Retrieving message chunk header", ec, httpclient_errorcode_context::readbody);
        }
    }

    void handle_chunk(const boost::system::error_code& ec, int to_read)
    {
        if (!ec)
        {
            m_timer.reset();

            m_downloaded += static_cast<uint64_t>(to_read);
            const auto &progress = m_request._get_impl()->_progress_handler();
            if (progress)
            {
                try
                {
                    (*progress)(message_direction::download, m_downloaded);
                }
                catch (...)
                {
                    report_exception(std::current_exception());
                    return;
                }
            }

            if (to_read == 0)
            {
                m_body_buf.consume(CRLF.size());
                complete_request(m_downloaded);
            }
            else
            {
                auto writeBuffer = _get_writebuffer();
                const auto this_request = shared_from_this();
                if(m_decompressor)
                {
                    auto decompressed = m_decompressor->decompress(boost::asio::buffer_cast<const uint8_t *>(m_body_buf.data()), to_read);

                    if (m_decompressor->has_error())
                    {
                        report_exception(std::runtime_error("Failed to decompress the response body"));
                        return;
                    }

                    // It is valid for the decompressor to sometimes return an empty output for a given chunk, the data will be flushed when the next chunk is received
                    if (decompressed.empty())
                    {
                        m_body_buf.consume(to_read + CRLF.size()); // consume crlf
                        m_connection->async_read_until(m_body_buf, CRLF, boost::bind(&asio_context::handle_chunk_header, this_request, boost::asio::placeholders::error));
                    }
                    else
                    {
                        // Move the decompressed buffer into a shared_ptr to keep it alive until putn_nocopy completes.
                        // When VS 2013 support is dropped, this should be changed to a unique_ptr plus a move capture.
                        using web::http::details::compression::data_buffer;
                        auto shared_decompressed = std::make_shared<data_buffer>(std::move(decompressed));

                        writeBuffer.putn_nocopy(shared_decompressed->data(), shared_decompressed->size())
                            .then([this_request, to_read, shared_decompressed](pplx::task<size_t> op)
                        {
                            try
                            {
                                op.get();
                                this_request->m_body_buf.consume(to_read + CRLF.size()); // consume crlf
                                this_request->m_connection->async_read_until(this_request->m_body_buf, CRLF, boost::bind(&asio_context::handle_chunk_header, this_request, boost::asio::placeholders::error));
                            }
                            catch (...)
                            {
                                this_request->report_exception(std::current_exception());
                                return;
                            }
                        });
                    }
                }
                else
                {
                    writeBuffer.putn_nocopy(boost::asio::buffer_cast<const uint8_t *>(m_body_buf.data()), to_read).then([this_request, to_read](pplx::task<size_t> op)
                    {
                        try
                        {
                            op.wait();
                        }
                        catch (...)
                        {
                            this_request->report_exception(std::current_exception());
                            return;
                        }
                        this_request->m_body_buf.consume(to_read + CRLF.size()); // consume crlf
                        this_request->m_connection->async_read_until(this_request->m_body_buf, CRLF, boost::bind(&asio_context::handle_chunk_header, this_request, boost::asio::placeholders::error));
                    }); 
                }
            }
        }
        else
        {
            report_error("Failed to read chunked response part", ec, httpclient_errorcode_context::readbody);
        }
    }

    void handle_read_content(const boost::system::error_code& ec)
    {
        auto writeBuffer = _get_writebuffer();


        if (ec)
        {
            if (ec == boost::asio::error::eof && m_content_length == std::numeric_limits<size_t>::max())
            {
                m_content_length = m_downloaded + m_body_buf.size();
            }
            else
            {
                report_error("Failed to read response body", ec, httpclient_errorcode_context::readbody);
                return;
            }
        }

        m_timer.reset();
        const auto &progress = m_request._get_impl()->_progress_handler();
        if (progress)
        {
            try
            {
                (*progress)(message_direction::download, m_downloaded);
            }
            catch (...)
            {
                report_exception(std::current_exception());
                return;
            }
        }

        if (m_downloaded < m_content_length)
        {
            // more data need to be read
            const auto this_request = shared_from_this();

            auto read_size = static_cast<size_t>(std::min(static_cast<uint64_t>(m_body_buf.size()), m_content_length - m_downloaded));

            if(m_decompressor)
            {
                auto decompressed = m_decompressor->decompress(boost::asio::buffer_cast<const uint8_t *>(m_body_buf.data()), read_size);
                
                if (m_decompressor->has_error())
                {
                    this_request->report_exception(std::runtime_error("Failed to decompress the response body"));
                    return;
                }

                // It is valid for the decompressor to sometimes return an empty output for a given chunk, the data will be flushed when the next chunk is received
                if (decompressed.empty())
                {
                    try
                    {
                        this_request->m_downloaded += static_cast<uint64_t>(read_size);

                        this_request->async_read_until_buffersize(static_cast<size_t>(std::min(static_cast<uint64_t>(this_request->m_http_client->client_config().chunksize()), this_request->m_content_length - this_request->m_downloaded)),
                            boost::bind(&asio_context::handle_read_content, this_request, boost::asio::placeholders::error));
                    }
                    catch (...)
                    {
                        this_request->report_exception(std::current_exception());
                        return;
                    }
                }
                else
                {
                    // Move the decompressed buffer into a shared_ptr to keep it alive until putn_nocopy completes.
                    // When VS 2013 support is dropped, this should be changed to a unique_ptr plus a move capture.
                    using web::http::details::compression::data_buffer;
                    auto shared_decompressed = std::make_shared<data_buffer>(std::move(decompressed));

                    writeBuffer.putn_nocopy(shared_decompressed->data(), shared_decompressed->size())
                        .then([this_request, read_size, shared_decompressed](pplx::task<size_t> op)
                    {
                        size_t writtenSize = 0;
                        try
                        {
                            writtenSize = op.get();
                            this_request->m_downloaded += static_cast<uint64_t>(read_size);
                            this_request->m_body_buf.consume(writtenSize);
                            this_request->async_read_until_buffersize(static_cast<size_t>(std::min(static_cast<uint64_t>(this_request->m_http_client->client_config().chunksize()), this_request->m_content_length - this_request->m_downloaded)),
                                boost::bind(&asio_context::handle_read_content, this_request, boost::asio::placeholders::error));
                        }
                        catch (...)
                        {
                            this_request->report_exception(std::current_exception());
                            return;
                        }
                    });
                }
            }
            else
            {
                writeBuffer.putn_nocopy(boost::asio::buffer_cast<const uint8_t *>(m_body_buf.data()), read_size)
                .then([this_request](pplx::task<size_t> op)
                {
                    size_t writtenSize = 0;
                    try
                    {
                        writtenSize = op.get();
                        this_request->m_downloaded += static_cast<uint64_t>(writtenSize);
                        this_request->m_body_buf.consume(writtenSize);
                        this_request->async_read_until_buffersize(static_cast<size_t>(std::min(static_cast<uint64_t>(this_request->m_http_client->client_config().chunksize()), this_request->m_content_length - this_request->m_downloaded)),
                                                                  boost::bind(&asio_context::handle_read_content, this_request, boost::asio::placeholders::error));
                    }
                    catch (...)
                    {
                        this_request->report_exception(std::current_exception());
                        return;
                    }
                });
            }
        }
        else
        {
            // Request is complete no more data to read.
            complete_request(m_downloaded);
        }
    }

    // Simple timer class wrapping Boost deadline timer.
    // Closes the connection when timer fires.
    class timeout_timer
    {
    public:

        timeout_timer(const std::chrono::microseconds& timeout) :
        m_duration(timeout.count()),
        m_state(created),
        m_timer(crossplat::threadpool::shared_instance().service())
        {}

        void set_ctx(const std::weak_ptr<asio_context> &ctx)
        {
            m_ctx = ctx;
        }

        void start()
        {
            assert(m_state == created);
            assert(!m_ctx.expired());
            m_state = started;

            m_timer.expires_from_now(m_duration);
            auto ctx = m_ctx;
            m_timer.async_wait([ctx](const boost::system::error_code& ec)
                               {
                                   handle_timeout(ec, ctx);
                               });
        }

        void reset()
        {
            assert(m_state == started || m_state == timedout);
            assert(!m_ctx.expired());
            if(m_timer.expires_from_now(m_duration) > 0)
            {
                // The existing handler was canceled so schedule a new one.
                assert(m_state == started);
                auto ctx = m_ctx;
                m_timer.async_wait([ctx](const boost::system::error_code& ec)
                {
                    handle_timeout(ec, ctx);
                });
            }
        }

        bool has_timedout() const { return m_state == timedout; }

        bool has_started() const { return m_state == started; }

        void stop()
        {
            m_state = stopped;
            m_timer.cancel();
        }

        static void handle_timeout(const boost::system::error_code& ec,
                                   const std::weak_ptr<asio_context> &ctx)
        {
            if(!ec)
            {
                auto shared_ctx = ctx.lock();
                if (shared_ctx)
                {
                    assert(shared_ctx->m_timer.m_state != timedout);
                    shared_ctx->m_timer.m_state = timedout;
                    shared_ctx->m_connection->close();
                }
            }
        }

    private:
        enum timer_state
        {
            created,
            started,
            stopped,
            timedout
        };

#if defined(ANDROID) || defined(__ANDROID__)
        boost::chrono::microseconds m_duration;
#else
        std::chrono::microseconds m_duration;
#endif
        std::atomic<timer_state> m_state;
        std::weak_ptr<asio_context> m_ctx;
        boost::asio::steady_timer m_timer;
    };

    uint64_t m_content_length;
    bool m_needChunked;
    timeout_timer m_timer;
    boost::asio::streambuf m_body_buf;
    std::shared_ptr<asio_connection> m_connection;
    
    std::unique_ptr<web::http::details::compression::stream_decompressor> m_decompressor;

#if defined(__APPLE__) || (defined(ANDROID) || defined(__ANDROID__))
    bool m_openssl_failed;
#endif
};


std::shared_ptr<_http_client_communicator> create_platform_final_pipeline_stage(uri&& base_uri, http_client_config&& client_config)
{
    return std::make_shared<asio_client>(std::move(base_uri), std::move(client_config));
}

void asio_client::send_request(const std::shared_ptr<request_context> &request_ctx)
{
    auto ctx = std::static_pointer_cast<asio_context>(request_ctx);

    try
    {
        if (ctx->m_connection->is_ssl())
        {
            client_config().invoke_nativehandle_options(ctx->m_connection->m_ssl_stream.get());
        }
        else 
        {
            client_config().invoke_nativehandle_options(&(ctx->m_connection->m_socket));
        }
    }
    catch (...)
    {
        request_ctx->report_exception(std::current_exception());
        return;
    }

    ctx->start_request();
}

pplx::task<http_response> asio_client::propagate(http_request request)
{
    auto self = std::static_pointer_cast<_http_client_communicator>(shared_from_this());
    auto context = details::asio_context::create_request_context(self, request);

    // Use a task to externally signal the final result and completion of the task.
    auto result_task = pplx::create_task(context->m_request_completion);

    // Asynchronously send the response with the HTTP client implementation.
    this->async_send_request(context);

    return result_task;
}

}}}} // namespaces
