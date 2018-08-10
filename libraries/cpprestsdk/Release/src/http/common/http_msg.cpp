/***
* Copyright (C) Microsoft. All rights reserved.
* Licensed under the MIT license. See LICENSE.txt file in the project root for full license information.
*
* =+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+
*
* HTTP Library: Request and reply message definitions.
*
* For the latest on this and related APIs, please see: https://github.com/Microsoft/cpprestsdk
*
* =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
****/
#include "stdafx.h"
#include "../common/internal_http_helpers.h"

#undef min
#undef max

using namespace web;
using namespace utility;
using namespace concurrency;
using namespace utility::conversions;
using namespace http::details;

namespace web { namespace http
{

#define CRLF _XPLATSTR("\r\n")

utility::string_t http_headers::content_type() const
{
    utility::string_t result;
    match(http::header_names::content_type, result);
    return result;
}



/// Helper functions to convert a series of bytes from a charset to utf-8 or utf-16.
/// These APIs deal with checking for and handling byte order marker (BOM).
namespace {
    enum endianness
    {
        little_endian,
        big_endian,
        unknown
    };
    endianness check_byte_order_mark(const utf16string &str)
    {
        if (str.empty())
        {
            return unknown;
        }
        const unsigned char *src = reinterpret_cast<const unsigned char *>(str.data());

        // little endian
        if (src[0] == 0xFF && src[1] == 0xFE)
        {
            return little_endian;
        }

        // big endian
        else if (src[0] == 0xFE && src[1] == 0xFF)
        {
            return big_endian;
        }

        return unknown;
    }

    std::string convert_utf16le_to_utf8(utf16string src, bool erase_bom)
    {
        if (erase_bom && !src.empty())
        {
            src.erase(0, 1);
        }
        return utf16_to_utf8(std::move(src));
    }

    utility::string_t convert_utf16le_to_string_t(utf16string src, bool erase_bom)
    {
        if (erase_bom && !src.empty())
        {
            src.erase(0, 1);
        }
    #ifdef _UTF16_STRINGS
        return src;
    #else
        return utf16_to_utf8(std::move(src));
    #endif
    }

    // Helper function to change endian ness from big endian to little endian
    utf16string big_endian_to_little_endian(utf16string src, bool erase_bom)
    {
        if (erase_bom && !src.empty())
        {
            src.erase(0, 1);
        }
        if (src.empty())
        {
            return src;
        }

        const size_t size = src.size();
        for (size_t i = 0; i < size; ++i)
        {
            utf16char ch = src[i];
            src[i] = static_cast<utf16char>(ch << 8);
            src[i] = static_cast<utf16char>(src[i] | ch >> 8);
        }

        return src;
    }

    std::string convert_utf16be_to_utf8(utf16string src, bool erase_bom)
    {
        return utf16_to_utf8(big_endian_to_little_endian(std::move(src), erase_bom));
    }

    utf16string convert_utf16be_to_utf16le(utf16string src, bool erase_bom)
    {
        return big_endian_to_little_endian(std::move(src), erase_bom);
    }

    utility::string_t convert_utf16be_to_string_t(utf16string src, bool erase_bom)
    {
    #ifdef _UTF16_STRINGS
        return convert_utf16be_to_utf16le(std::move(src), erase_bom);
    #else
        return convert_utf16be_to_utf8(std::move(src), erase_bom);
    #endif
    }

    std::string convert_utf16_to_utf8(utf16string src)
    {
        const endianness endian = check_byte_order_mark(src);
        switch (endian)
        {
        case little_endian:
            return convert_utf16le_to_utf8(std::move(src), true);
        case big_endian:
            return convert_utf16be_to_utf8(std::move(src), true);
        case unknown:
            // unknown defaults to big endian.
            return convert_utf16be_to_utf8(std::move(src), false);
        }
        __assume(0);
    }

    utf16string convert_utf16_to_utf16(utf16string src)
    {
        const endianness endian = check_byte_order_mark(src);
        switch (endian)
        {
        case little_endian:
            src.erase(0, 1);
            return src;
        case big_endian:
            return convert_utf16be_to_utf16le(std::move(src), true);
        case unknown:
            // unknown defaults to big endian.
            return convert_utf16be_to_utf16le(std::move(src), false);
        }
        __assume(0);
    }
    utility::string_t convert_utf16_to_string_t(utf16string src)
    {
    #ifdef _UTF16_STRINGS
        return convert_utf16_to_utf16(std::move(src));
    #else
        return convert_utf16_to_utf8(std::move(src));
    #endif
    }
}

void http_headers::set_content_type(utility::string_t type)
{
    m_headers[http::header_names::content_type] = std::move(type);
}

utility::string_t http_headers::cache_control() const
{
    utility::string_t result;
    match(http::header_names::cache_control, result);
    return result;
}

void http_headers::set_cache_control(utility::string_t control)
{
    add(http::header_names::cache_control, std::move(control));
}

utility::string_t http_headers::date() const
{
    utility::string_t result;
    match(http::header_names::date, result);
    return result;
}

void http_headers::set_date(const utility::datetime& date)
{
    m_headers[http::header_names::date] = date.to_string(utility::datetime::RFC_1123);
}

utility::size64_t http_headers::content_length() const
{
    utility::size64_t length = 0;
    match(http::header_names::content_length, length);
    return length;
}

void http_headers::set_content_length(utility::size64_t length)
{
    m_headers[http::header_names::content_length] = utility::conversions::details::to_string_t(length);
}

namespace details {

utility::string_t flatten_http_headers(const http_headers &headers)
{
    utility::string_t flattened_headers;
    for (auto iter = headers.begin(); iter != headers.end(); ++iter)
    {
        flattened_headers.append(iter->first);
        flattened_headers.push_back(':');
        flattened_headers.append(iter->second);
        flattened_headers.append(CRLF);
    }
    return flattened_headers;
}

#if defined(_WIN32)
void parse_headers_string(_Inout_z_ utf16char *headersStr, http_headers &headers)
{
    utf16char *context = nullptr;
    utf16char *line = wcstok_s(headersStr, CRLF, &context);
    while (line != nullptr)
    {
        const utility::string_t header_line(line);
        const size_t colonIndex = header_line.find_first_of(_XPLATSTR(":"));
        if (colonIndex != utility::string_t::npos)
        {
            utility::string_t key = header_line.substr(0, colonIndex);
            utility::string_t value = header_line.substr(colonIndex + 1, header_line.length() - colonIndex - 1);
            http::details::trim_whitespace(key);
            http::details::trim_whitespace(value);
            headers.add(key, value);
        }
        line = wcstok_s(nullptr, CRLF, &context);
    }
}
#endif

}

static const utility::char_t * stream_was_set_explicitly = _XPLATSTR("A stream was set on the message and extraction is not possible");
static const utility::char_t * unsupported_charset = _XPLATSTR("Charset must be iso-8859-1, utf-8, utf-16, utf-16le, or utf-16be to be extracted.");

http_msg_base::http_msg_base()
    : m_headers(),
      m_default_outstream(false)
{
}

void http_msg_base::_prepare_to_receive_data()
{
    // See if the user specified an outstream
    if (!outstream())
    {
        // The user did not specify an outstream.
        // We will create one...
        concurrency::streams::producer_consumer_buffer<uint8_t> buf;
        set_outstream(buf.create_ostream(), true);

        // Since we are creating the streambuffer, set the input stream
        // so that the user can retrieve the data.
        set_instream(buf.create_istream());
    }

    // If the user did specify an outstream we leave the instream
    // as invalid. It is assumed that user either has a read head
    // to the out streambuffer or the data is streamed into a container
    // or media (like file) that the user can read from...
}

size_t http_msg_base::_get_content_length()
{
    // An invalid response_stream indicates that there is no body
    if ((bool)instream())
    {
        size_t content_length = 0;
        utility::string_t transfer_encoding;

        bool has_cnt_length = headers().match(header_names::content_length, content_length);
        bool has_xfr_encode = headers().match(header_names::transfer_encoding, transfer_encoding);

        if (has_xfr_encode)
        {
            return std::numeric_limits<size_t>::max();
        }

        if (has_cnt_length)
        {
            return content_length;
        }

        // Neither is set. Assume transfer-encoding for now (until we have the ability to determine
        // the length of the stream).
        headers().add(header_names::transfer_encoding, _XPLATSTR("chunked"));
        return std::numeric_limits<size_t>::max();
    }

    return 0;
}

// Helper function to inline continuation if possible.
struct inline_continuation
{
    inline_continuation(pplx::task<void> &prev, const std::function<void(pplx::task<void>)> &next) : m_prev(prev), m_next(next) {}
    ~inline_continuation()
    {
        if (m_prev.is_done())
        {
            m_next(m_prev);
        }
        else
        {
            m_prev.then(m_next);
        }
    }
    pplx::task<void> & m_prev;
    std::function<void(pplx::task<void>)> m_next;
private:
    inline_continuation(const inline_continuation &);
    inline_continuation &operator=(const inline_continuation &);
};

void http_msg_base::_complete(utility::size64_t body_size, const std::exception_ptr &exceptionPtr)
{
    const auto &completionEvent = _get_data_available();
    auto closeTask = pplx::task_from_result();

    if (exceptionPtr == std::exception_ptr())
    {
        if (m_default_outstream)
        {
            closeTask = outstream().close();
        }

        inline_continuation(closeTask, [completionEvent, body_size](pplx::task<void> t)
        {
            try
            {
                t.get();
                completionEvent.set(body_size);
            }
            catch (...)
            {
                // If close throws an exception report back to user.
                completionEvent.set_exception(std::current_exception());
                pplx::create_task(completionEvent).then([](pplx::task<utility::size64_t> t)
                {
                    try { t.get(); }
                    catch (...) {}
                });
            }
        });
    }
    else
    {
        if (outstream().is_valid())
        {
            closeTask = outstream().close(exceptionPtr);
        }

        inline_continuation(closeTask, [completionEvent, exceptionPtr](pplx::task<void> t)
        {
            // If closing stream throws an exception ignore since we already have an error.
            try { t.get(); }
            catch (...) {}
            completionEvent.set_exception(exceptionPtr);
            pplx::create_task(completionEvent).then([](pplx::task<utility::size64_t> t)
            {
                try { t.get(); }
                catch (...) {}
            });
        });
    }
}

static bool is_content_type_one_of(const utility::string_t *first, const utility::string_t *last, const utility::string_t &value)
{
    while (first != last)
    {
        if (utility::details::str_icmp(*first, value))
        {
            return true;
        }
        ++first;
    }
    return false;
}

// Remove once VS 2013 is no longer supported.
#if defined(_WIN32) && _MSC_VER < 1900
// Not referring to mime_types to avoid static initialization order fiasco.
static const utility::string_t textual_types [] = {
    U("message/http"),
    U("application/json"),
    U("application/xml"),
    U("application/atom+xml"),
    U("application/http"),
    U("application/x-www-form-urlencoded")
};
#endif

/// <summary>
/// Determines whether or not the given content type is 'textual' according the feature specifications.
/// </summary>
static bool is_content_type_textual(const utility::string_t &content_type)
{
#if !defined(_WIN32) || _MSC_VER >= 1900
    static const utility::string_t textual_types [] = {
        mime_types::message_http,
        mime_types::application_json,
        mime_types::application_xml,
        mime_types::application_atom_xml,
        mime_types::application_http,
        mime_types::application_x_www_form_urlencoded
    };
#endif

    if (content_type.size() >= 4 && utility::details::str_icmp(content_type.substr(0, 4), _XPLATSTR("text")))
    {
        return true;
    }
    return (is_content_type_one_of(std::begin(textual_types), std::end(textual_types), content_type));
}

// Remove once VS 2013 is no longer supported.
#if defined(_WIN32) && _MSC_VER < 1900
// Not referring to mime_types to avoid static initialization order fiasco.
static const utility::string_t json_types [] = {
    U("application/json"),
    U("application/x-json"),
    U("text/json"),
    U("text/x-json"),
    U("text/javascript"),
    U("text/x-javascript"),
    U("application/javascript"),
    U("application/x-javascript")
};
#endif

/// <summary>
/// Determines whether or not the given content type is JSON according the feature specifications.
/// </summary>
static bool is_content_type_json(const utility::string_t &content_type)
{
#if !defined(_WIN32) || _MSC_VER >= 1900
    static const utility::string_t json_types [] = {
        mime_types::application_json,
        mime_types::application_xjson,
        mime_types::text_json,
        mime_types::text_xjson,
        mime_types::text_javascript,
        mime_types::text_xjavascript,
        mime_types::application_javascript,
        mime_types::application_xjavascript
    };
#endif

    return (is_content_type_one_of(std::begin(json_types), std::end(json_types), content_type));
}

/// <summary>
/// Gets the default charset for given content type. If the MIME type is not textual or recognized Latin1 will be returned.
/// </summary>
static utility::string_t get_default_charset(const utility::string_t &content_type)
{
    // We are defaulting everything to Latin1 except JSON which is utf-8.
    if (is_content_type_json(content_type))
    {
        return charset_types::utf8;
    }
    else
    {
        return charset_types::latin1;
    }
}


/// <summary>
/// Parses the given Content-Type header value to get out actual content type and charset.
/// If the charset isn't specified the default charset for the content type will be set.
/// </summary>
static void parse_content_type_and_charset(const utility::string_t &content_type, utility::string_t &content, utility::string_t &charset)
{
    const size_t semi_colon_index = content_type.find_first_of(_XPLATSTR(";"));

    // No charset specified.
    if (semi_colon_index == utility::string_t::npos)
    {
        content = content_type;
        trim_whitespace(content);
        charset = get_default_charset(content);
        return;
    }

    // Split into content type and second part which could be charset.
    content = content_type.substr(0, semi_colon_index);
    trim_whitespace(content);
    utility::string_t possible_charset = content_type.substr(semi_colon_index + 1);
    trim_whitespace(possible_charset);
    const size_t equals_index = possible_charset.find_first_of(_XPLATSTR("="));

    // No charset specified.
    if (equals_index == utility::string_t::npos)
    {
        charset = get_default_charset(content);
        return;
    }

    // Split and make sure 'charset'
    utility::string_t charset_key = possible_charset.substr(0, equals_index);
    trim_whitespace(charset_key);
    if (!utility::details::str_icmp(charset_key, _XPLATSTR("charset")))
    {
        charset = get_default_charset(content);
        return;
    }
    charset = possible_charset.substr(equals_index + 1);
    // Remove the redundant ';' at the end of charset.
    while (charset.back() == ';')
    {
        charset.pop_back();
    }
    trim_whitespace(charset);
    if (charset.front() == _XPLATSTR('"') && charset.back() == _XPLATSTR('"'))
    {
        charset = charset.substr(1, charset.size() - 2);
        trim_whitespace(charset);
    }
}

utility::string_t details::http_msg_base::parse_and_check_content_type(bool ignore_content_type, const std::function<bool(const utility::string_t &)> &check_content_type)
{
    if (!instream())
    {
        throw http_exception(stream_was_set_explicitly);
    }

    utility::string_t content, charset = charset_types::utf8;
    if (!ignore_content_type)
    {
        parse_content_type_and_charset(headers().content_type(), content, charset);

        // If no Content-Type or empty body then just return an empty string.
        if (content.empty() || instream().streambuf().in_avail() == 0)
        {
            return utility::string_t();
        }

        if (!check_content_type(content))
        {
            throw http_exception(_XPLATSTR("Incorrect Content-Type: must be textual to extract_string, JSON to extract_json."));
        }
    }
    return charset;
}

utf8string details::http_msg_base::extract_utf8string(bool ignore_content_type)
{
    const auto &charset = parse_and_check_content_type(ignore_content_type, is_content_type_textual);
    if (charset.empty())
    {
        return utf8string();
    }
    auto buf_r = instream().streambuf();

    // Perform the correct character set conversion if one is necessary.
    if (utility::details::str_icmp(charset, charset_types::utf8)
        || utility::details::str_icmp(charset, charset_types::usascii)
        || utility::details::str_icmp(charset, charset_types::ascii))
    {
        std::string body;
        body.resize((std::string::size_type)buf_r.in_avail());
        buf_r.getn(const_cast<uint8_t *>(reinterpret_cast<const uint8_t *>(body.data())), body.size()).get(); // There is no risk of blocking.
        return body;
    }

    // Latin1
    else if (utility::details::str_icmp(charset, charset_types::latin1))
    {
        std::string body;
        body.resize((std::string::size_type)buf_r.in_avail());
        buf_r.getn(const_cast<uint8_t *>(reinterpret_cast<const uint8_t *>(body.data())), body.size()).get(); // There is no risk of blocking.
        return latin1_to_utf8(std::move(body));
    }

    // utf-16
    else if (utility::details::str_icmp(charset, charset_types::utf16))
    {
        utf16string body;
        body.resize(buf_r.in_avail() / sizeof(utf16string::value_type));
        buf_r.getn(const_cast<uint8_t *>(reinterpret_cast<const uint8_t *>(body.data())), body.size() * sizeof(utf16string::value_type)); // There is no risk of blocking.
        return convert_utf16_to_utf8(std::move(body));
    }

    // utf-16le
    else if (utility::details::str_icmp(charset, charset_types::utf16le))
    {
        utf16string body;
        body.resize(buf_r.in_avail() / sizeof(utf16string::value_type));
        buf_r.getn(const_cast<uint8_t *>(reinterpret_cast<const uint8_t *>(body.data())), body.size() * sizeof(utf16string::value_type)); // There is no risk of blocking.
        return utility::conversions::utf16_to_utf8(std::move(body));
    }

    // utf-16be
    else if (utility::details::str_icmp(charset, charset_types::utf16be))
    {
        utf16string body;
        body.resize(buf_r.in_avail() / sizeof(utf16string::value_type));
        buf_r.getn(const_cast<uint8_t *>(reinterpret_cast<const uint8_t *>(body.data())), body.size() * sizeof(utf16string::value_type)); // There is no risk of blocking.
        return convert_utf16be_to_utf8(std::move(body), false);
    }

    else
    {
        throw http_exception(unsupported_charset);
    }
}

utf16string details::http_msg_base::extract_utf16string(bool ignore_content_type)
{
    const auto &charset = parse_and_check_content_type(ignore_content_type, is_content_type_textual);
    if (charset.empty())
    {
        return utf16string();
    }
    auto buf_r = instream().streambuf();

    // Perform the correct character set conversion if one is necessary.
    if (utility::details::str_icmp(charset, charset_types::utf16le))
    {
        utf16string body;
        body.resize(buf_r.in_avail() / sizeof(utf16string::value_type));
        buf_r.getn(const_cast<uint8_t *>(reinterpret_cast<const uint8_t *>(body.data())), body.size() * sizeof(utf16string::value_type)); // There is no risk of blocking.
        return body;
    }

    // utf-8, ascii
    else if (utility::details::str_icmp(charset, charset_types::utf8)
        || utility::details::str_icmp(charset, charset_types::usascii)
        || utility::details::str_icmp(charset, charset_types::ascii))
    {
        std::string body;
        body.resize((std::string::size_type)buf_r.in_avail());
        buf_r.getn(const_cast<uint8_t *>(reinterpret_cast<const uint8_t *>(body.data())), body.size()).get(); // There is no risk of blocking.
        return utility::conversions::utf8_to_utf16(std::move(body));
    }

    // Latin1
    else if (utility::details::str_icmp(charset, charset_types::latin1))
    {
        std::string body;
        body.resize((std::string::size_type)buf_r.in_avail());
        buf_r.getn(const_cast<uint8_t *>(reinterpret_cast<const uint8_t *>(body.data())), body.size()).get(); // There is no risk of blocking.
        return latin1_to_utf16(std::move(body));
    }

    // utf-16
    else if (utility::details::str_icmp(charset, charset_types::utf16))
    {
        utf16string body;
        body.resize(buf_r.in_avail() / sizeof(utf16string::value_type));
        buf_r.getn(const_cast<uint8_t *>(reinterpret_cast<const uint8_t *>(body.data())), body.size() * sizeof(utf16string::value_type)); // There is no risk of blocking.
        return convert_utf16_to_utf16(std::move(body));
    }

    // utf-16be
    else if (utility::details::str_icmp(charset, charset_types::utf16be))
    {
        utf16string body;
        body.resize(buf_r.in_avail() / sizeof(utf16string::value_type));
        buf_r.getn(const_cast<uint8_t *>(reinterpret_cast<const uint8_t *>(body.data())), body.size() * sizeof(utf16string::value_type)); // There is no risk of blocking.
        return convert_utf16be_to_utf16le(std::move(body), false);
    }

    else
    {
        throw http_exception(unsupported_charset);
    }
}

utility::string_t details::http_msg_base::extract_string(bool ignore_content_type)
{
    const auto &charset = parse_and_check_content_type(ignore_content_type, is_content_type_textual);
    if (charset.empty())
    {
        return utility::string_t();
    }
    auto buf_r = instream().streambuf();

    // Perform the correct character set conversion if one is necessary.
    if (utility::details::str_icmp(charset, charset_types::usascii)
            || utility::details::str_icmp(charset, charset_types::ascii))
    {
        std::string body;
        body.resize((std::string::size_type)buf_r.in_avail());
        buf_r.getn(const_cast<uint8_t *>(reinterpret_cast<const uint8_t *>(body.data())), body.size()).get(); // There is no risk of blocking.
        return to_string_t(std::move(body));
    }

    // Latin1
    if(utility::details::str_icmp(charset, charset_types::latin1))
    {
        std::string body;
        body.resize((std::string::size_type)buf_r.in_avail());
        buf_r.getn(const_cast<uint8_t *>(reinterpret_cast<const uint8_t *>(body.data())), body.size()).get(); // There is no risk of blocking.
        // Could optimize for linux in the future if a latin1_to_utf8 function was written.
        return to_string_t(latin1_to_utf16(std::move(body)));
    }

    // utf-8.
    else if(utility::details::str_icmp(charset, charset_types::utf8))
    {
        std::string body;
        body.resize((std::string::size_type)buf_r.in_avail());
        buf_r.getn(const_cast<uint8_t *>(reinterpret_cast<const uint8_t *>(body.data())), body.size()).get(); // There is no risk of blocking.
        return to_string_t(std::move(body));
    }

    // utf-16.
    else if(utility::details::str_icmp(charset, charset_types::utf16))
    {
        utf16string body;
        body.resize(buf_r.in_avail() / sizeof(utf16string::value_type));
        buf_r.getn(const_cast<uint8_t *>(reinterpret_cast<const uint8_t *>(body.data())), body.size() * sizeof(utf16string::value_type)); // There is no risk of blocking.
        return convert_utf16_to_string_t(std::move(body));
    }

    // utf-16le
    else if(utility::details::str_icmp(charset, charset_types::utf16le))
    {
        utf16string body;
        body.resize(buf_r.in_avail() / sizeof(utf16string::value_type));
        buf_r.getn(const_cast<uint8_t *>(reinterpret_cast<const uint8_t *>(body.data())), body.size() * sizeof(utf16string::value_type)); // There is no risk of blocking.
        return convert_utf16le_to_string_t(std::move(body), false);
    }

    // utf-16be
    else if(utility::details::str_icmp(charset, charset_types::utf16be))
    {
        utf16string body;
        body.resize(buf_r.in_avail() / sizeof(utf16string::value_type));
        buf_r.getn(const_cast<uint8_t *>(reinterpret_cast<const uint8_t *>(body.data())), body.size() * sizeof(utf16string::value_type)); // There is no risk of blocking.
        return convert_utf16be_to_string_t(std::move(body), false);
    }

    else
    {
        throw http_exception(unsupported_charset);
    }
}

json::value details::http_msg_base::_extract_json(bool ignore_content_type)
{
    const auto &charset = parse_and_check_content_type(ignore_content_type, is_content_type_json);
    if (charset.empty())
    {
        return json::value();
    }
    auto buf_r = instream().streambuf();

    // Latin1
    if(utility::details::str_icmp(charset, charset_types::latin1))
    {
        std::string body;
        body.resize(buf_r.in_avail());
        buf_r.getn(const_cast<uint8_t *>(reinterpret_cast<const uint8_t *>(body.data())), body.size()).get(); // There is no risk of blocking.
        // On Linux could optimize in the future if a latin1_to_utf8 function is written.
        return json::value::parse(to_string_t(latin1_to_utf16(std::move(body))));
    }

    // utf-8, usascii and ascii
    else if(utility::details::str_icmp(charset, charset_types::utf8)
            || utility::details::str_icmp(charset, charset_types::usascii)
            || utility::details::str_icmp(charset, charset_types::ascii))
    {
        std::string body;
        body.resize(buf_r.in_avail());
        buf_r.getn(const_cast<uint8_t *>(reinterpret_cast<const uint8_t *>(body.data())), body.size()).get(); // There is no risk of blocking.
        return json::value::parse(to_string_t(std::move(body)));
    }

    // utf-16.
    else if(utility::details::str_icmp(charset, charset_types::utf16))
    {
        utf16string body;
        body.resize(buf_r.in_avail() / sizeof(utf16string::value_type));
        buf_r.getn(const_cast<uint8_t *>(reinterpret_cast<const uint8_t *>(body.data())), body.size() * sizeof(utf16string::value_type)); // There is no risk of blocking.
        return json::value::parse(convert_utf16_to_string_t(std::move(body)));
    }

    // utf-16le
    else if(utility::details::str_icmp(charset, charset_types::utf16le))
    {
        utf16string body;
        body.resize(buf_r.in_avail() / sizeof(utf16string::value_type));
        buf_r.getn(const_cast<uint8_t *>(reinterpret_cast<const uint8_t *>(body.data())), body.size() * sizeof(utf16string::value_type)); // There is no risk of blocking.
        return json::value::parse(convert_utf16le_to_string_t(std::move(body), false));
    }

    // utf-16be
    else if(utility::details::str_icmp(charset, charset_types::utf16be))
    {
        utf16string body;
        body.resize(buf_r.in_avail() / sizeof(utf16string::value_type));
        buf_r.getn(const_cast<uint8_t *>(reinterpret_cast<const uint8_t *>(body.data())), body.size() * sizeof(utf16string::value_type)); // There is no risk of blocking.
        return json::value::parse(convert_utf16be_to_string_t(std::move(body), false));
    }

    else
    {
        throw http_exception(unsupported_charset);
    }
}

std::vector<uint8_t> details::http_msg_base::_extract_vector()
{
    if (!instream())
    {
        throw http_exception(stream_was_set_explicitly);
    }

    std::vector<uint8_t> body;
    auto buf_r = instream().streambuf();
    const size_t size = buf_r.in_avail();
    body.resize(size);
    buf_r.getn(const_cast<uint8_t *>(reinterpret_cast<const uint8_t *>(body.data())), size).get(); // There is no risk of blocking.

    return body;
}

// Helper function to convert message body without extracting.
static utility::string_t convert_body_to_string_t(const utility::string_t &content_type, concurrency::streams::istream instream)
{
    if (!instream)
    {
        // The instream is not yet set
        return utility::string_t();
    }

    concurrency::streams::streambuf<uint8_t>  streambuf = instream.streambuf();

    _ASSERTE((bool)streambuf);
    _ASSERTE(streambuf.is_open());
    _ASSERTE(streambuf.can_read());

    utility::string_t content, charset;
    parse_content_type_and_charset(content_type, content, charset);

    // Content-Type must have textual type.
    if(!is_content_type_textual(content) || streambuf.in_avail() == 0)
    {
        return utility::string_t();
    }

    // Latin1
    if(utility::details::str_icmp(charset, charset_types::latin1))
    {
        std::string body;
        body.resize(streambuf.in_avail());
        if(streambuf.scopy((unsigned char *)&body[0], body.size()) == 0) return string_t();
        return to_string_t(latin1_to_utf16(std::move(body)));
    }

    // utf-8.
    else if(utility::details::str_icmp(charset, charset_types::utf8))
    {
        std::string body;
        body.resize(streambuf.in_avail());
        if(streambuf.scopy((unsigned char *)&body[0], body.size()) == 0) return string_t();
        return to_string_t(std::move(body));
    }

    // utf-16.
    else if(utility::details::str_icmp(charset, charset_types::utf16))
    {
        utf16string body;
        body.resize(streambuf.in_avail() / sizeof(utf16string::value_type));
        if(streambuf.scopy((unsigned char *)&body[0], body.size() * sizeof(utf16string::value_type)) == 0) return string_t();
        return convert_utf16_to_string_t(std::move(body));
    }

    // utf-16le
    else if(utility::details::str_icmp(charset, charset_types::utf16le))
    {
        utf16string body;
        body.resize(streambuf.in_avail() / sizeof(utf16string::value_type));
        if(streambuf.scopy((unsigned char *)&body[0], body.size() * sizeof(utf16string::value_type)) == 0) return string_t();
        return convert_utf16le_to_string_t(std::move(body), false);
    }

    // utf-16be
    else if(utility::details::str_icmp(charset, charset_types::utf16be))
    {
        utf16string body;
        body.resize(streambuf.in_avail() / sizeof(utf16string::value_type));
        if(streambuf.scopy((unsigned char *)&body[0], body.size() * sizeof(utf16string::value_type)) == 0) return string_t();
        return convert_utf16be_to_string_t(std::move(body), false);
    }

    else
    {
        return utility::string_t();
    }
}

//
// Helper function to generate a wstring from given http_headers and message body.
//
static utility::string_t http_headers_body_to_string(const http_headers &headers, concurrency::streams::istream instream)
{
    utility::ostringstream_t buffer;
    buffer.imbue(std::locale::classic());

    for (const auto &header : headers)
    {
        buffer << header.first << _XPLATSTR(": ") << header.second << CRLF;
    }
    buffer << CRLF;

    utility::string_t content_type;
    if(headers.match(http::header_names::content_type, content_type))
    {
        buffer << convert_body_to_string_t(content_type, instream);
    }

    return buffer.str();
}

utility::string_t details::http_msg_base::to_string() const
{
    return http_headers_body_to_string(m_headers, instream());
}

static void set_content_type_if_not_present(http::http_headers &headers, const utility::string_t &content_type)
{
    utility::string_t temp;
    if(!headers.match(http::header_names::content_type, temp))
    {
        headers.add(http::header_names::content_type, content_type);
    }
}

void details::http_msg_base::set_body(const streams::istream &instream, const utf8string &contentType)
{
    set_content_type_if_not_present(
    		headers(),
#ifdef _UTF16_STRINGS
    		utility::conversions::utf8_to_utf16(contentType));
#else
    		contentType);
#endif
    set_instream(instream);
}

void details::http_msg_base::set_body(const streams::istream &instream, const utf16string &contentType)
{
    set_content_type_if_not_present(
    		headers(),
#ifdef _UTF16_STRINGS
    		contentType);
#else
    		utility::conversions::utf16_to_utf8(contentType));
#endif
    set_instream(instream);
}

void details::http_msg_base::set_body(const streams::istream &instream, utility::size64_t contentLength, const utf8string &contentType)
{
    headers().set_content_length(contentLength);
    set_body(instream, contentType);
    m_data_available.set(contentLength);
}

void details::http_msg_base::set_body(const concurrency::streams::istream &instream, utility::size64_t contentLength, const utf16string &contentType)
{
    headers().set_content_length(contentLength);
    set_body(instream, contentType);
    m_data_available.set(contentLength);
}

details::_http_request::_http_request(http::method mtd)
  : m_method(std::move(mtd)),
    m_initiated_response(0),
    m_server_context(),
    m_cancellationToken(pplx::cancellation_token::none())
{
    if(m_method.empty())
    {
        throw std::invalid_argument("Invalid HTTP method specified. Method can't be an empty string.");
    }
}

details::_http_request::_http_request(std::unique_ptr<http::details::_http_server_context> server_context)
  : m_initiated_response(0),
    m_server_context(std::move(server_context)),
    m_cancellationToken(pplx::cancellation_token::none())
{
}

#define _METHODS
#define DAT(a,b) const method methods::a = b;
#include "cpprest/details/http_constants.dat"
#undef _METHODS
#undef DAT

#define _HEADER_NAMES
#define DAT(a,b) const utility::string_t header_names::a = _XPLATSTR(b);
#include "cpprest/details/http_constants.dat"
#undef _HEADER_NAMES
#undef DAT

#define _MIME_TYPES
#define DAT(a,b) const utility::string_t mime_types::a = _XPLATSTR(b);
#include "cpprest/details/http_constants.dat"
#undef _MIME_TYPES
#undef DAT

#define _CHARSET_TYPES
#define DAT(a,b) const utility::string_t charset_types::a = _XPLATSTR(b);
#include "cpprest/details/http_constants.dat"
#undef _CHARSET_TYPES
#undef DAT

// This is necessary for Linux because of a bug in GCC 4.7
#ifndef _WIN32
#define _PHRASES
#define DAT(a,b,c) const status_code status_codes::a;
#include "cpprest/details/http_constants.dat"
#undef _PHRASES
#undef DAT
#endif
}} // namespace web::http

