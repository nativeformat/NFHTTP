# Copyright (c) 2018 Spotify AB.
#
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
add_library(sqlite "${CMAKE_CURRENT_SOURCE_DIR}/sqlite/sqlite3.c")
target_compile_definitions(sqlite PUBLIC -DSQLITE_THREADSAFE=2)

set(BOOST_MAJOR 1)
set(BOOST_MINOR 64)
set(BOOST_PATCH 0)
set(BOOST_VER_DOT "${BOOST_MAJOR}.${BOOST_MINOR}.${BOOST_PATCH}")
set(BOOST_VER_UNDER "${BOOST_MAJOR}_${BOOST_MINOR}_${BOOST_PATCH}")
if(APPLE OR ANDROID)
  set(OPENSSL_ROOT_DIR "${CMAKE_CURRENT_SOURCE_DIR}/openssl")
  execute_process(COMMAND wget http://sourceforge.net/projects/boost/files/boost/${BOOST_VER_DOT}/boost_${BOOST_VER_UNDER}.tar.gz -O ${CMAKE_CURRENT_SOURCE_DIR}/boost_${BOOST_VER_UNDER}.tar.gz)
  execute_process(COMMAND tar -xzf ${CMAKE_CURRENT_SOURCE_DIR}/boost_${BOOST_VER_UNDER}.tar.gz -C ${CMAKE_CURRENT_SOURCE_DIR})
  set(BOOST_EXTRACTION_FOLDER_STRIPPED ${CMAKE_CURRENT_SOURCE_DIR})
  set(BOOST_EXTRACTION_FOLDER "${CMAKE_CURRENT_SOURCE_DIR}/boost_${BOOST_VER_UNDER}")
  set(BOOST_LIB_DIR "${BOOST_EXTRACTION_FOLDER_STRIPPED}/boost_${BOOST_VER_UNDER}/libs")
  set(BOOST_ROOT "${CMAKE_CURRENT_SOURCE_DIR}/boost_${BOOST_VER_UNDER}")
endif(APPLE OR ANDROID)

message(STATUS "Finding Boost")
if(NOT ANDROID)
  find_package(Boost ${BOOST_VER_DOT} REQUIRED)
else(NOT ANDROID)
  set(BOOST_LIB_DIR "${BOOST_EXTRACTION_FOLDER_STRIPPED}/boost_${BOOST_VER_UNDER}/libs")
  set(BOOST_GRAPH_SRC_DIR "${BOOST_LIB_DIR}/graph/src")
  set(BOOST_PROGRAM_OPTIONS_SRC_DIR "${BOOST_LIB_DIR}/program_options/src")
  set(BOOST_THREAD_SRC_DIR "${BOOST_LIB_DIR}/thread/src")
  set(BOOST_CHRONO_SRC_DIR "${BOOST_LIB_DIR}/chrono/src")
  set(BOOST_SYSTEM_SRC_DIR "${BOOST_LIB_DIR}/system/src")
  set(BOOST_TEST_SRC_DIR "${BOOST_LIB_DIR}/test/src")
  set(BOOST_RANDOM_SRC_DIR "${BOOST_LIB_DIR}/random/src")
  set(BOOST_FILESYSTEM_SRC_DIR "${BOOST_LIB_DIR}/filesystem/src")
  set(BOOST_ATOMIC_SRC_DIR "${BOOST_LIB_DIR}/atomic/src")
  set(BOOST_DATE_TIME_SRC_DIR "${BOOST_LIB_DIR}/date_time/src")
  set(BOOST_REGEX_SRC_DIR "${BOOST_LIB_DIR}/regex/src")
  add_library(boost_graph STATIC
    ${BOOST_GRAPH_SRC_DIR}/graphml.cpp
    ${BOOST_GRAPH_SRC_DIR}/read_graphviz_new.cpp)
  add_library(boost_program_options STATIC
    ${BOOST_PROGRAM_OPTIONS_SRC_DIR}/cmdline.cpp
    ${BOOST_PROGRAM_OPTIONS_SRC_DIR}/config_file.cpp
    ${BOOST_PROGRAM_OPTIONS_SRC_DIR}/convert.cpp
    ${BOOST_PROGRAM_OPTIONS_SRC_DIR}/options_description.cpp
    ${BOOST_PROGRAM_OPTIONS_SRC_DIR}/parsers.cpp
    ${BOOST_PROGRAM_OPTIONS_SRC_DIR}/positional_options.cpp
    ${BOOST_PROGRAM_OPTIONS_SRC_DIR}/split.cpp
    ${BOOST_PROGRAM_OPTIONS_SRC_DIR}/utf8_codecvt_facet.cpp
    ${BOOST_PROGRAM_OPTIONS_SRC_DIR}/value_semantic.cpp
    ${BOOST_PROGRAM_OPTIONS_SRC_DIR}/variables_map.cpp
    ${BOOST_PROGRAM_OPTIONS_SRC_DIR}/winmain.cpp)
  add_library(boost_thread STATIC
    #${BOOST_THREAD_SRC_DIR}/win32/tss_dll.cpp
    #${BOOST_THREAD_SRC_DIR}/win32/tss_pe.cpp
    #${BOOST_THREAD_SRC_DIR}/win32/thread.cpp
    ${BOOST_THREAD_SRC_DIR}/future.cpp
    ${BOOST_THREAD_SRC_DIR}/tss_null.cpp
    ${BOOST_THREAD_SRC_DIR}/pthread/once_atomic.cpp
    ${BOOST_THREAD_SRC_DIR}/pthread/once.cpp
    ${BOOST_THREAD_SRC_DIR}/pthread/thread.cpp)
  add_library(boost_chrono STATIC
    ${BOOST_CHRONO_SRC_DIR}/chrono.cpp
    ${BOOST_CHRONO_SRC_DIR}/process_cpu_clocks.cpp
    ${BOOST_CHRONO_SRC_DIR}/thread_clock.cpp)
  add_library(boost_system STATIC
    ${BOOST_SYSTEM_SRC_DIR}/error_code.cpp)
  add_library(boost_test STATIC
    ${BOOST_TEST_SRC_DIR}/compiler_log_formatter.cpp
    #${BOOST_TEST_SRC_DIR}/cpp_main.cpp
    ${BOOST_TEST_SRC_DIR}/debug.cpp
    ${BOOST_TEST_SRC_DIR}/decorator.cpp
    ${BOOST_TEST_SRC_DIR}/execution_monitor.cpp
    ${BOOST_TEST_SRC_DIR}/framework.cpp
    ${BOOST_TEST_SRC_DIR}/junit_log_formatter.cpp
    ${BOOST_TEST_SRC_DIR}/plain_report_formatter.cpp
    ${BOOST_TEST_SRC_DIR}/progress_monitor.cpp
    ${BOOST_TEST_SRC_DIR}/results_collector.cpp
    ${BOOST_TEST_SRC_DIR}/results_reporter.cpp
    ${BOOST_TEST_SRC_DIR}/test_main.cpp
    ${BOOST_TEST_SRC_DIR}/test_tools.cpp
    ${BOOST_TEST_SRC_DIR}/test_tree.cpp
    ${BOOST_TEST_SRC_DIR}/unit_test_log.cpp
    ${BOOST_TEST_SRC_DIR}/unit_test_main.cpp
    ${BOOST_TEST_SRC_DIR}/unit_test_monitor.cpp
    ${BOOST_TEST_SRC_DIR}/unit_test_parameters.cpp
    ${BOOST_TEST_SRC_DIR}/xml_log_formatter.cpp
    ${BOOST_TEST_SRC_DIR}/xml_report_formatter.cpp)

  file(GLOB SRC_FILES ${BOOST_RANDOM_SRC_DIR}/*.cpp)
  add_library(boost_random STATIC ${SRC_FILES})
  file(GLOB SRC_FILES ${BOOST_FILESYSTEM_SRC_DIR}/*.cpp)
  add_library(boost_filesystem STATIC ${SRC_FILES})
  file(GLOB SRC_FILES ${BOOST_ATOMIC_SRC_DIR}/*.cpp)
  add_library(boost_atomic STATIC ${SRC_FILES})
  file(GLOB SRC_FILES ${BOOST_REGEX_SRC_DIR}/*.cpp)
  add_library(boost_regex STATIC ${SRC_FILES})
  add_library(boost_date_time INTERFACE)

  set(Boost_GRAPH_LIBRARY boost_graph)
  set(Boost_PROGRAM_OPTIONS_LIBRARY boost_program_options)
  set(Boost_THREAD_LIBRARY boost_thread)
  set(Boost_CHRONO_LIBRARY boost_chrono)
  set(Boost_SYSTEM_LIBRARY boost_system)
  set(Boost_TEST_LIBRARY boost_test)
  set(Boost_RANDOM_LIBRARY boost_random)
  set(Boost_FILESYSTEM_LIBRARY boost_filesystem)
  set(Boost_ATOMIC_LIBRARY boost_atomic)
  set(Boost_REGEX_LIBRARY boost_regex)
  set(Boost_DATE_TIME_LIBRARY boost_date_time)
  set(Boost_INCLUDE_DIR "${BOOST_EXTRACTION_FOLDER_STRIPPED}/boost_1_64_0")
  set(Boost_INCLUDE_DIR ${Boost_INCLUDE_DIR} CACHE STRING "Boost headers" FORCE)
  target_include_directories(boost_graph PUBLIC ${Boost_INCLUDE_DIR})
  target_include_directories(boost_program_options PUBLIC ${Boost_INCLUDE_DIR})
  target_include_directories(boost_thread PUBLIC ${Boost_INCLUDE_DIR})
  target_include_directories(boost_chrono PUBLIC ${Boost_INCLUDE_DIR})
  target_include_directories(boost_system PUBLIC ${Boost_INCLUDE_DIR})
  target_include_directories(boost_test PUBLIC ${Boost_INCLUDE_DIR})
  target_include_directories(boost_random PUBLIC ${Boost_INCLUDE_DIR})
  target_include_directories(boost_filesystem PUBLIC ${Boost_INCLUDE_DIR})
  target_include_directories(boost_atomic PUBLIC ${Boost_INCLUDE_DIR})
  target_include_directories(boost_regex PUBLIC ${Boost_INCLUDE_DIR})
  target_include_directories(boost_date_time INTERFACE ${Boost_INCLUDE_DIR})

  set(Boost_LIBRARIES
    ${BOOST_GRAPH_LIBRARY}
    ${Boost_PROGRAM_OPTIONS_LIBRARY}
    ${Boost_THREAD_LIBRARY}
    ${Boost_CHRONO_LIBRARY}
    ${Boost_SYSTEM_LIBRARY}
    ${Boost_TEST_LIBRARY}
    CACHE INTERNAL "Boost libraries")
  set(Boost_FOUND 1)
  set(Boost_FOUND 1 PARENT_SCOPE)
endif(NOT ANDROID)

message(STATUS "Finding OpenSSL")
if(NOT ANDROID)
  find_package(OpenSSL 1.0.0 REQUIRED)
endif(NOT ANDROID)
if(NOT OPENSSL_FOUND OR OPENSSL_NFHTTP_ADDED)
  message(STATUS "OpenSSL not found on system, will use submodule instead")
  set(OPENSSL_FOUND ON CACHE BOOL "OpenSSL is found" FORCE)
  set(OpenSSL_FOUND ON CACHE BOOL "OpenSSL is found" FORCE)
  set(OPENSSL_NFHTTP_ADDED ON CACHE BOOL "OpenSSL added by NFHTTP" FORCE)
  set(OPENSSL_DIR "${CMAKE_CURRENT_SOURCE_DIR}/openssl")
  set(OPENSSL_INCLUDE_DIR "${OPENSSL_DIR}/include" CACHE STRING "OpenSSL Includes" FORCE)
  set(OPENSSL_VERSION "1.0.0" CACHE STRING "OpenSSL Version" FORCE)
  message(STATUS "Make Results:")
  execute_process(COMMAND sh ${OPENSSL_DIR}/config no-asm
    WORKING_DIRECTORY ${OPENSSL_DIR})
  message(STATUS "End Make Results")
  execute_process(COMMAND make include/openssl/opensslconf.h
    WORKING_DIRECTORY "${OPENSSL_DIR}")
  set(OPENSSL_CRYPTO_DIR "${OPENSSL_DIR}/crypto")
  set(OPENSSL_AES_DIR "${OPENSSL_CRYPTO_DIR}/aes")
  set(OPENSSL_MODES_DIR "${OPENSSL_CRYPTO_DIR}/modes")
  set(OPENSSL_RSA_DIR "${OPENSSL_CRYPTO_DIR}/rsa")
  set(OPENSSL_ASN1_DIR "${OPENSSL_CRYPTO_DIR}/asn1")
  set(OPENSSL_EVP_DIR "${OPENSSL_CRYPTO_DIR}/evp")
  set(OPENSSL_BIO_DIR "${OPENSSL_CRYPTO_DIR}/bio")
  set(OPENSSL_BN_DIR "${OPENSSL_CRYPTO_DIR}/bn")
  set(OPENSSL_BUFFER_DIR "${OPENSSL_CRYPTO_DIR}/buffer")
  set(OPENSSL_CMAC_DIR "${OPENSSL_CRYPTO_DIR}/cmac")
  set(OPENSSL_CONF_DIR "${OPENSSL_CRYPTO_DIR}/conf")
  set(OPENSSL_DSO_DIR "${OPENSSL_CRYPTO_DIR}/dso")
  set(OPENSSL_ENGINE_DIR "${OPENSSL_CRYPTO_DIR}/engine")
  set(OPENSSL_ERROR_DIR "${OPENSSL_CRYPTO_DIR}/err")
  set(OPENSSL_X509_DIR "${OPENSSL_CRYPTO_DIR}/x509")
  set(OPENSSL_X509V3_DIR "${OPENSSL_CRYPTO_DIR}/x509v3")
  set(OPENSSL_CMS_DIR "${OPENSSL_CRYPTO_DIR}/cms")
  set(OPENSSL_EVP_DIR "${OPENSSL_CRYPTO_DIR}/evp")
  set(OPENSSL_BF_DIR "${OPENSSL_CRYPTO_DIR}/bf")
  set(OPENSSL_CAST_DIR "${OPENSSL_CRYPTO_DIR}/cast")
  set(OPENSSL_CAMELLIA_DIR "${OPENSSL_CRYPTO_DIR}/camellia")
  set(OPENSSL_DES_DIR "${OPENSSL_CRYPTO_DIR}/des")
  set(OPENSSL_DH_DIR "${OPENSSL_CRYPTO_DIR}/dh")
  set(OPENSSL_DSA_DIR "${OPENSSL_CRYPTO_DIR}/dsa")
  set(OPENSSL_ECDSA_DIR "${OPENSSL_CRYPTO_DIR}/ecdsa")
  set(OPENSSL_EC_DIR "${OPENSSL_CRYPTO_DIR}/ec")
  set(OPENSSL_ECDH_DIR "${OPENSSL_CRYPTO_DIR}/ecdh")
  set(OPENSSL_COMP_DIR "${OPENSSL_CRYPTO_DIR}/comp")
  set(OPENSSL_SSL_DIR "${OPENSSL_DIR}/ssl")
  set(OPENSSL_OBJECTS_DIR "${OPENSSL_CRYPTO_DIR}/objects")
  set(OPENSSL_OCSP_DIR "${OPENSSL_CRYPTO_DIR}/ocsp")
  set(OPENSSL_PEM_DIR "${OPENSSL_CRYPTO_DIR}/pem")
  set(OPENSSL_PKCS12_DIR "${OPENSSL_CRYPTO_DIR}/pkcs12")
  set(OPENSSL_PKCS7_DIR "${OPENSSL_CRYPTO_DIR}/pkcs7")
  set(OPENSSL_RAND_DIR "${OPENSSL_CRYPTO_DIR}/rand")
  set(OPENSSL_TS_DIR "${OPENSSL_CRYPTO_DIR}/ts")
  set(OPENSSL_UI_DIR "${OPENSSL_CRYPTO_DIR}/ui")
  set(OPENSSL_HMAC_DIR "${OPENSSL_CRYPTO_DIR}/hmac")
  set(OPENSSL_MD4_DIR "${OPENSSL_CRYPTO_DIR}/md4")
  set(OPENSSL_MD5_DIR "${OPENSSL_CRYPTO_DIR}/md5")
  set(OPENSSL_MDC2_DIR "${OPENSSL_CRYPTO_DIR}/mdc2")
  set(OPENSSL_RC2_DIR "${OPENSSL_CRYPTO_DIR}/rc2")
  set(OPENSSL_RC4_DIR "${OPENSSL_CRYPTO_DIR}/rc4")
  set(OPENSSL_RIPEMD_DIR "${OPENSSL_CRYPTO_DIR}/ripemd")
  set(OPENSSL_SEED_DIR "${OPENSSL_CRYPTO_DIR}/seed")
  set(OPENSSL_SHA_DIR "${OPENSSL_CRYPTO_DIR}/sha")
  set(OPENSSL_SRP_DIR "${OPENSSL_CRYPTO_DIR}/srp")
  set(OPENSSL_TXT_DB_DIR "${OPENSSL_CRYPTO_DIR}/txt_db")
  set(OPENSSL_WHRLPOOL_DIR "${OPENSSL_CRYPTO_DIR}/whrlpool")
  set(OPENSSL_IDEA_DIR "${OPENSSL_CRYPTO_DIR}/idea")
  set(OPENSSL_LHASH_DIR "${OPENSSL_CRYPTO_DIR}/lhash")
  set(OPENSSL_PQUEUE_DIR "${OPENSSL_CRYPTO_DIR}/pqueue")
  set(OPENSSL_STACK_DIR "${OPENSSL_CRYPTO_DIR}/stack")
  add_library(openssl_crypto STATIC ${OPENSSL_CRYPTO_DIR}/arm_arch.h
                                    #${OPENSSL_CRYPTO_DIR}/buildinf.h
                                    ${OPENSSL_CRYPTO_DIR}/constant_time_locl.h
                                    ${OPENSSL_CRYPTO_DIR}/cpt_err.c
                                    ${OPENSSL_CRYPTO_DIR}/cryptlib.c
                                    ${OPENSSL_CRYPTO_DIR}/cryptlib.h
                                    ${OPENSSL_CRYPTO_DIR}/crypto.h
                                    #${OPENSSL_CRYPTO_DIR}/cversion.c
                                    ${OPENSSL_CRYPTO_DIR}/ebcdic.c
                                    ${OPENSSL_CRYPTO_DIR}/ebcdic.h
                                    ${OPENSSL_CRYPTO_DIR}/ex_data.c
                                    ${OPENSSL_CRYPTO_DIR}/fips_err.h
                                    ${OPENSSL_CRYPTO_DIR}/md32_common.h
                                    ${OPENSSL_CRYPTO_DIR}/mem_clr.c
                                    ${OPENSSL_CRYPTO_DIR}/mem_dbg.c
                                    ${OPENSSL_CRYPTO_DIR}/mem.c
                                    ${OPENSSL_CRYPTO_DIR}/o_dir.c
                                    ${OPENSSL_CRYPTO_DIR}/o_dir.h
                                    ${OPENSSL_CRYPTO_DIR}/o_fips.c
                                    ${OPENSSL_CRYPTO_DIR}/o_init.c
                                    ${OPENSSL_CRYPTO_DIR}/o_str.h
                                    ${OPENSSL_CRYPTO_DIR}/o_time.c
                                    ${OPENSSL_CRYPTO_DIR}/o_time.h
                                    ${OPENSSL_CRYPTO_DIR}/opensslconf.h
                                    ${OPENSSL_CRYPTO_DIR}/opensslv.h
                                    ${OPENSSL_CRYPTO_DIR}/ossl_typ.h
                                    ${OPENSSL_CRYPTO_DIR}/ppc_arch.h
                                    ${OPENSSL_CRYPTO_DIR}/sparc_arch.h
                                    ${OPENSSL_CRYPTO_DIR}/symhacks.h
                                    ${OPENSSL_CRYPTO_DIR}/uid.c
                                    ${OPENSSL_CRYPTO_DIR}/vms_rms.h)
  add_library(openssl STATIC ${OPENSSL_AES_DIR}/aes_cbc.c
                             ${OPENSSL_AES_DIR}/aes_cfb.c
                             ${OPENSSL_AES_DIR}/aes_core.c
                             ${OPENSSL_AES_DIR}/aes_ctr.c
                             ${OPENSSL_AES_DIR}/aes_ecb.c
                             ${OPENSSL_AES_DIR}/aes_ige.c
                             ${OPENSSL_AES_DIR}/aes_locl.h
                             ${OPENSSL_AES_DIR}/aes_misc.c
                             ${OPENSSL_AES_DIR}/aes_ofb.c
                             ${OPENSSL_AES_DIR}/aes_wrap.c
                             ${OPENSSL_AES_DIR}/aes_x86core.c
                             ${OPENSSL_AES_DIR}/aes.h
                             ${OPENSSL_MODES_DIR}/cbc128.c
                             ${OPENSSL_MODES_DIR}/ccm128.c
                             ${OPENSSL_MODES_DIR}/cfb128.c
                             ${OPENSSL_MODES_DIR}/ctr128.c
                             ${OPENSSL_MODES_DIR}/cts128.c
                             ${OPENSSL_MODES_DIR}/gcm128.c
                             ${OPENSSL_MODES_DIR}/modes_lcl.h
                             ${OPENSSL_MODES_DIR}/modes.h
                             ${OPENSSL_MODES_DIR}/wrap128.c
                             ${OPENSSL_MODES_DIR}/ofb128.c
                             ${OPENSSL_MODES_DIR}/xts128.c
                             ${OPENSSL_RSA_DIR}/rsa_ameth.c
                             ${OPENSSL_RSA_DIR}/rsa_asn1.c
                             ${OPENSSL_RSA_DIR}/rsa_crpt.c
                             ${OPENSSL_RSA_DIR}/rsa_depr.c
                             ${OPENSSL_RSA_DIR}/rsa_eay.c
                             ${OPENSSL_RSA_DIR}/rsa_err.c
                             ${OPENSSL_RSA_DIR}/rsa_gen.c
                             ${OPENSSL_RSA_DIR}/rsa_lib.c
                             ${OPENSSL_RSA_DIR}/rsa_none.c
                             ${OPENSSL_RSA_DIR}/rsa_null.c
                             ${OPENSSL_RSA_DIR}/rsa_oaep.c
                             ${OPENSSL_RSA_DIR}/rsa_pk1.c
                             ${OPENSSL_RSA_DIR}/rsa_pmeth.c
                             ${OPENSSL_RSA_DIR}/rsa_prn.c
                             ${OPENSSL_RSA_DIR}/rsa_pss.c
                             ${OPENSSL_RSA_DIR}/rsa_saos.c
                             ${OPENSSL_RSA_DIR}/rsa_sign.c
                             ${OPENSSL_RSA_DIR}/rsa_ssl.c
                             ${OPENSSL_RSA_DIR}/rsa.h
                             ${OPENSSL_RSA_DIR}/rsa_x931.c
                             ${OPENSSL_RSA_DIR}/rsa_chk.c
                             ${OPENSSL_BIO_DIR}/b_dump.c
                             ${OPENSSL_BIO_DIR}/b_print.c
                             ${OPENSSL_BIO_DIR}/b_sock.c
                             ${OPENSSL_BIO_DIR}/bf_buff.c
                             ${OPENSSL_BIO_DIR}/bf_lbuf.c
                             ${OPENSSL_BIO_DIR}/bf_nbio.c
                             ${OPENSSL_BIO_DIR}/bf_null.c
                             ${OPENSSL_BIO_DIR}/bio_cb.c
                             ${OPENSSL_BIO_DIR}/bio_err.c
                             ${OPENSSL_BIO_DIR}/bio_lcl.h
                             ${OPENSSL_BIO_DIR}/bio_lib.c
                             ${OPENSSL_BIO_DIR}/bio.h
                             ${OPENSSL_BIO_DIR}/bss_acpt.c
                             ${OPENSSL_BIO_DIR}/bss_bio.c
                             ${OPENSSL_BIO_DIR}/bss_conn.c
                             ${OPENSSL_BIO_DIR}/bss_dgram.c
                             ${OPENSSL_BIO_DIR}/bss_fd.c
                             ${OPENSSL_BIO_DIR}/bss_file.c
                             ${OPENSSL_BIO_DIR}/bss_log.c
                             ${OPENSSL_BIO_DIR}/bss_mem.c
                             ${OPENSSL_BIO_DIR}/bss_null.c
                             ${OPENSSL_BIO_DIR}/bss_sock.c
                             ${OPENSSL_BN_DIR}/bn_add.c
                             ${OPENSSL_BN_DIR}/bn_asm.c
                             ${OPENSSL_BN_DIR}/bn_blind.c
                             ${OPENSSL_BN_DIR}/bn_const.c
                             ${OPENSSL_BN_DIR}/bn_ctx.c
                             ${OPENSSL_BN_DIR}/bn_depr.c
                             ${OPENSSL_BN_DIR}/bn_div.c
                             ${OPENSSL_BN_DIR}/bn_err.c
                             ${OPENSSL_BN_DIR}/bn_exp.c
                             ${OPENSSL_BN_DIR}/bn_exp2.c
                             ${OPENSSL_BN_DIR}/bn_gcd.c
                             ${OPENSSL_BN_DIR}/bn_gf2m.c
                             ${OPENSSL_BN_DIR}/bn_kron.c
                             ${OPENSSL_BN_DIR}/bn_lcl.h
                             ${OPENSSL_BN_DIR}/bn_lib.c
                             ${OPENSSL_BN_DIR}/bn_mod.c
                             ${OPENSSL_BN_DIR}/bn_mont.c
                             ${OPENSSL_BN_DIR}/bn_mpi.c
                             ${OPENSSL_BN_DIR}/bn_mul.c
                             ${OPENSSL_BN_DIR}/bn_nist.c
                             ${OPENSSL_BN_DIR}/bn_prime.c
                             ${OPENSSL_BN_DIR}/bn_prime.h
                             ${OPENSSL_BN_DIR}/bn_print.c
                             ${OPENSSL_BN_DIR}/bn_rand.c
                             ${OPENSSL_BN_DIR}/bn_recp.c
                             ${OPENSSL_BN_DIR}/bn_shift.c
                             ${OPENSSL_BN_DIR}/bn_sqr.c
                             ${OPENSSL_BN_DIR}/bn_sqrt.c
                             ${OPENSSL_BN_DIR}/bn_word.c
                             ${OPENSSL_BN_DIR}/bn_x931p.c
                             ${OPENSSL_BN_DIR}/bn.h
                             ${OPENSSL_BN_DIR}/bnspeed.c
                             ${OPENSSL_BN_DIR}/expspeed.c
                             ${OPENSSL_BN_DIR}/rsaz_exp.c
                             ${OPENSSL_BN_DIR}/rsaz_exp.h
                             ${OPENSSL_BUFFER_DIR}/buf_err.c
                             ${OPENSSL_BUFFER_DIR}/buf_str.c
                             ${OPENSSL_BUFFER_DIR}/buffer.c
                             ${OPENSSL_BUFFER_DIR}/buffer.h
                             ${OPENSSL_CMAC_DIR}/cm_ameth.c
                             ${OPENSSL_CMAC_DIR}/cm_pmeth.c
                             ${OPENSSL_CMAC_DIR}/cmac.c
                             ${OPENSSL_CMAC_DIR}/cmac.h
                             ${OPENSSL_CONF_DIR}/conf_api.c
                             ${OPENSSL_CONF_DIR}/conf_api.h
                             ${OPENSSL_CONF_DIR}/conf_def.c
                             ${OPENSSL_CONF_DIR}/conf_def.h
                             ${OPENSSL_CONF_DIR}/conf_err.c
                             ${OPENSSL_CONF_DIR}/conf_lib.c
                             ${OPENSSL_CONF_DIR}/conf_mall.c
                             ${OPENSSL_CONF_DIR}/conf_mod.c
                             ${OPENSSL_CONF_DIR}/conf_sap.c
                             ${OPENSSL_CONF_DIR}/conf.h
                             ${OPENSSL_DSO_DIR}/dso_beos.c
                             ${OPENSSL_DSO_DIR}/dso_dl.c
                             ${OPENSSL_DSO_DIR}/dso_dlfcn.c
                             ${OPENSSL_DSO_DIR}/dso_err.c
                             ${OPENSSL_DSO_DIR}/dso_lib.c
                             ${OPENSSL_DSO_DIR}/dso_null.c
                             ${OPENSSL_DSO_DIR}/dso_openssl.c
                             ${OPENSSL_DSO_DIR}/dso_vms.c
                             ${OPENSSL_DSO_DIR}/dso_win32.c
                             ${OPENSSL_DSO_DIR}/dso.h
                             ${OPENSSL_ENGINE_DIR}/eng_all.c
                             ${OPENSSL_ENGINE_DIR}/eng_cnf.c
                             ${OPENSSL_ENGINE_DIR}/eng_cryptodev.c
                             ${OPENSSL_ENGINE_DIR}/eng_ctrl.c
                             ${OPENSSL_ENGINE_DIR}/eng_dyn.c
                             ${OPENSSL_ENGINE_DIR}/eng_err.c
                             ${OPENSSL_ENGINE_DIR}/eng_fat.c
                             ${OPENSSL_ENGINE_DIR}/eng_init.c
                             ${OPENSSL_ENGINE_DIR}/eng_int.h
                             ${OPENSSL_ENGINE_DIR}/eng_lib.c
                             ${OPENSSL_ENGINE_DIR}/eng_list.c
                             ${OPENSSL_ENGINE_DIR}/eng_openssl.c
                             ${OPENSSL_ENGINE_DIR}/eng_pkey.c
                             ${OPENSSL_ENGINE_DIR}/eng_rdrand.c
                             ${OPENSSL_ENGINE_DIR}/eng_table.c
                             ${OPENSSL_ENGINE_DIR}/engine.h
                             ${OPENSSL_ENGINE_DIR}/tb_asnmth.c
                             ${OPENSSL_ENGINE_DIR}/tb_cipher.c
                             ${OPENSSL_ENGINE_DIR}/tb_dh.c
                             ${OPENSSL_ENGINE_DIR}/tb_digest.c
                             ${OPENSSL_ENGINE_DIR}/tb_dsa.c
                             ${OPENSSL_ENGINE_DIR}/tb_ecdh.c
                             ${OPENSSL_ENGINE_DIR}/tb_ecdsa.c
                             ${OPENSSL_ENGINE_DIR}/tb_pkmeth.c
                             ${OPENSSL_ENGINE_DIR}/tb_rand.c
                             ${OPENSSL_ENGINE_DIR}/tb_rsa.c
                             ${OPENSSL_ENGINE_DIR}/tb_store.c
                             ${OPENSSL_ERROR_DIR}/err_all.c
                             ${OPENSSL_ERROR_DIR}/err_prn.c
                             ${OPENSSL_ERROR_DIR}/err.c
                             ${OPENSSL_ERROR_DIR}/err.h
                             ${OPENSSL_ASN1_DIR}/a_bitstr.c
                             ${OPENSSL_ASN1_DIR}/a_bool.c
                             ${OPENSSL_ASN1_DIR}/a_bytes.c
                             ${OPENSSL_ASN1_DIR}/a_d2i_fp.c
                             ${OPENSSL_ASN1_DIR}/a_digest.c
                             ${OPENSSL_ASN1_DIR}/a_dup.c
                             ${OPENSSL_ASN1_DIR}/a_enum.c
                             ${OPENSSL_ASN1_DIR}/a_gentm.c
                             ${OPENSSL_ASN1_DIR}/a_i2d_fp.c
                             ${OPENSSL_ASN1_DIR}/a_int.c
                             ${OPENSSL_ASN1_DIR}/a_mbstr.c
                             ${OPENSSL_ASN1_DIR}/a_object.c
                             ${OPENSSL_ASN1_DIR}/a_octet.c
                             ${OPENSSL_ASN1_DIR}/a_print.c
                             ${OPENSSL_ASN1_DIR}/a_set.c
                             ${OPENSSL_ASN1_DIR}/a_sign.c
                             ${OPENSSL_ASN1_DIR}/a_strex.c
                             ${OPENSSL_ASN1_DIR}/a_strnid.c
                             ${OPENSSL_ASN1_DIR}/a_time.c
                             ${OPENSSL_ASN1_DIR}/a_type.c
                             ${OPENSSL_ASN1_DIR}/a_utctm.c
                             ${OPENSSL_ASN1_DIR}/a_utf8.c
                             ${OPENSSL_ASN1_DIR}/a_verify.c
                             ${OPENSSL_ASN1_DIR}/ameth_lib.c
                             ${OPENSSL_ASN1_DIR}/asn_mime.c
                             ${OPENSSL_ASN1_DIR}/asn_moid.c
                             ${OPENSSL_ASN1_DIR}/asn_pack.c
                             ${OPENSSL_ASN1_DIR}/asn1_err.c
                             ${OPENSSL_ASN1_DIR}/asn1_lib.c
                             ${OPENSSL_ASN1_DIR}/asn1_locl.h
                             ${OPENSSL_ASN1_DIR}/asn1_mac.h
                             ${OPENSSL_ASN1_DIR}/asn1_par.c
                             ${OPENSSL_ASN1_DIR}/asn1.h
                             ${OPENSSL_ASN1_DIR}/asn1t.h
                             ${OPENSSL_ASN1_DIR}/bio_asn1.c
                             ${OPENSSL_ASN1_DIR}/bio_ndef.c
                             ${OPENSSL_ASN1_DIR}/charmap.h
                             ${OPENSSL_ASN1_DIR}/d2i_pr.c
                             ${OPENSSL_ASN1_DIR}/d2i_pu.c
                             ${OPENSSL_ASN1_DIR}/evp_asn1.c
                             ${OPENSSL_ASN1_DIR}/f_enum.c
                             ${OPENSSL_ASN1_DIR}/f_int.c
                             ${OPENSSL_ASN1_DIR}/f_string.c
                             ${OPENSSL_ASN1_DIR}/i2d_pr.c
                             ${OPENSSL_ASN1_DIR}/i2d_pu.c
                             ${OPENSSL_ASN1_DIR}/n_pkey.c
                             ${OPENSSL_ASN1_DIR}/nsseq.c
                             ${OPENSSL_ASN1_DIR}/p5_pbe.c
                             ${OPENSSL_ASN1_DIR}/p5_pbev2.c
                             ${OPENSSL_ASN1_DIR}/p8_pkey.c
                             ${OPENSSL_ASN1_DIR}/t_bitst.c
                             ${OPENSSL_ASN1_DIR}/t_crl.c
                             ${OPENSSL_ASN1_DIR}/t_pkey.c
                             ${OPENSSL_ASN1_DIR}/t_req.c
                             ${OPENSSL_ASN1_DIR}/t_spki.c
                             ${OPENSSL_ASN1_DIR}/t_x509.c
                             ${OPENSSL_ASN1_DIR}/t_x509a.c
                             ${OPENSSL_ASN1_DIR}/tasn_dec.c
                             ${OPENSSL_ASN1_DIR}/tasn_enc.c
                             ${OPENSSL_ASN1_DIR}/tasn_fre.c
                             ${OPENSSL_ASN1_DIR}/tasn_new.c
                             ${OPENSSL_ASN1_DIR}/tasn_prn.c
                             ${OPENSSL_ASN1_DIR}/tasn_typ.c
                             ${OPENSSL_ASN1_DIR}/tasn_utl.c
                             ${OPENSSL_ASN1_DIR}/x_algor.c
                             ${OPENSSL_ASN1_DIR}/x_attrib.c
                             ${OPENSSL_ASN1_DIR}/x_bignum.c
                             ${OPENSSL_ASN1_DIR}/x_crl.c
                             ${OPENSSL_ASN1_DIR}/x_exten.c
                             ${OPENSSL_ASN1_DIR}/x_info.c
                             ${OPENSSL_ASN1_DIR}/x_long.c
                             ${OPENSSL_ASN1_DIR}/x_name.c
                             ${OPENSSL_ASN1_DIR}/x_nx509.c
                             ${OPENSSL_ASN1_DIR}/x_pkey.c
                             ${OPENSSL_ASN1_DIR}/x_pubkey.c
                             ${OPENSSL_ASN1_DIR}/x_req.c
                             ${OPENSSL_ASN1_DIR}/x_sig.c
                             ${OPENSSL_ASN1_DIR}/x_spki.c
                             ${OPENSSL_ASN1_DIR}/x_val.c
                             ${OPENSSL_ASN1_DIR}/x_x509.c
                             ${OPENSSL_ASN1_DIR}/x_x509a.c
                             ${OPENSSL_ASN1_DIR}/asn1_gen.c
                             ${OPENSSL_X509_DIR}/by_dir.c
                             ${OPENSSL_X509_DIR}/by_file.c
                             ${OPENSSL_X509_DIR}/vpm_int.h
                             ${OPENSSL_X509_DIR}/x_all.c
                             ${OPENSSL_X509_DIR}/x509_att.c
                             ${OPENSSL_X509_DIR}/x509_cmp.c
                             ${OPENSSL_X509_DIR}/x509_d2.c
                             ${OPENSSL_X509_DIR}/x509_def.c
                             ${OPENSSL_X509_DIR}/x509_err.c
                             ${OPENSSL_X509_DIR}/x509_ext.c
                             ${OPENSSL_X509_DIR}/x509_lu.c
                             ${OPENSSL_X509_DIR}/x509_obj.c
                             ${OPENSSL_X509_DIR}/x509_r2x.c
                             ${OPENSSL_X509_DIR}/x509_req.c
                             ${OPENSSL_X509_DIR}/x509_set.c
                             ${OPENSSL_X509_DIR}/x509_trs.c
                             ${OPENSSL_X509_DIR}/x509_txt.c
                             ${OPENSSL_X509_DIR}/x509_v3.c
                             ${OPENSSL_X509_DIR}/x509_vfy.c
                             ${OPENSSL_X509_DIR}/x509_vfy.h
                             ${OPENSSL_X509_DIR}/x509_vpm.c
                             ${OPENSSL_X509_DIR}/x509.h
                             ${OPENSSL_X509_DIR}/x509cset.c
                             ${OPENSSL_X509_DIR}/x509name.c
                             ${OPENSSL_X509_DIR}/x509rset.c
                             ${OPENSSL_X509_DIR}/x509spki.c
                             ${OPENSSL_X509_DIR}/x509type.c
                             ${OPENSSL_X509V3_DIR}/ext_dat.h
                             ${OPENSSL_X509V3_DIR}/pcy_cache.c
                             ${OPENSSL_X509V3_DIR}/pcy_data.c
                             ${OPENSSL_X509V3_DIR}/pcy_int.h
                             ${OPENSSL_X509V3_DIR}/pcy_lib.c
                             ${OPENSSL_X509V3_DIR}/pcy_map.c
                             ${OPENSSL_X509V3_DIR}/pcy_node.c
                             ${OPENSSL_X509V3_DIR}/pcy_tree.c
                             ${OPENSSL_X509V3_DIR}/v3_addr.c
                             ${OPENSSL_X509V3_DIR}/v3_akey.c
                             ${OPENSSL_X509V3_DIR}/v3_akeya.c
                             ${OPENSSL_X509V3_DIR}/v3_alt.c
                             ${OPENSSL_X509V3_DIR}/v3_asid.c
                             ${OPENSSL_X509V3_DIR}/v3_bcons.c
                             ${OPENSSL_X509V3_DIR}/v3_bitst.c
                             ${OPENSSL_X509V3_DIR}/v3_conf.c
                             ${OPENSSL_X509V3_DIR}/v3_cpols.c
                             ${OPENSSL_X509V3_DIR}/v3_crld.c
                             ${OPENSSL_X509V3_DIR}/v3_enum.c
                             ${OPENSSL_X509V3_DIR}/v3_extku.c
                             ${OPENSSL_X509V3_DIR}/v3_genn.c
                             ${OPENSSL_X509V3_DIR}/v3_ia5.c
                             ${OPENSSL_X509V3_DIR}/v3_info.c
                             ${OPENSSL_X509V3_DIR}/v3_int.c
                             ${OPENSSL_X509V3_DIR}/v3_lib.c
                             ${OPENSSL_X509V3_DIR}/v3_ncons.c
                             ${OPENSSL_X509V3_DIR}/v3_ocsp.c
                             ${OPENSSL_X509V3_DIR}/v3_pci.c
                             ${OPENSSL_X509V3_DIR}/v3_pcia.c
                             ${OPENSSL_X509V3_DIR}/v3_pcons.c
                             ${OPENSSL_X509V3_DIR}/v3_pku.c
                             ${OPENSSL_X509V3_DIR}/v3_pmaps.c
                             ${OPENSSL_X509V3_DIR}/v3_prn.c
                             ${OPENSSL_X509V3_DIR}/v3_purp.c
                             ${OPENSSL_X509V3_DIR}/v3_scts.c
                             ${OPENSSL_X509V3_DIR}/v3_skey.c
                             ${OPENSSL_X509V3_DIR}/v3_sxnet.c
                             ${OPENSSL_X509V3_DIR}/v3_utl.c
                             ${OPENSSL_X509V3_DIR}/v3err.c
                             ${OPENSSL_X509V3_DIR}/x509v3.h
                             ${OPENSSL_CMS_DIR}/cms_asn1.c
                             ${OPENSSL_CMS_DIR}/cms_att.c
                             ${OPENSSL_CMS_DIR}/cms_cd.c
                             ${OPENSSL_CMS_DIR}/cms_dd.c
                             ${OPENSSL_CMS_DIR}/cms_enc.c
                             ${OPENSSL_CMS_DIR}/cms_env.c
                             ${OPENSSL_CMS_DIR}/cms_err.c
                             ${OPENSSL_CMS_DIR}/cms_ess.c
                             ${OPENSSL_CMS_DIR}/cms_io.c
                             ${OPENSSL_CMS_DIR}/cms_kari.c
                             ${OPENSSL_CMS_DIR}/cms_lcl.h
                             ${OPENSSL_CMS_DIR}/cms_lib.c
                             ${OPENSSL_CMS_DIR}/cms_pwri.c
                             ${OPENSSL_CMS_DIR}/cms_sd.c
                             ${OPENSSL_CMS_DIR}/cms_smime.c
                             ${OPENSSL_CMS_DIR}/cms.h
                             ${OPENSSL_EVP_DIR}/bio_b64.c
                             ${OPENSSL_EVP_DIR}/bio_enc.c
                             ${OPENSSL_EVP_DIR}/bio_md.c
                             ${OPENSSL_EVP_DIR}/bio_ok.c
                             ${OPENSSL_EVP_DIR}/c_all.c
                             ${OPENSSL_EVP_DIR}/c_allc.c
                             ${OPENSSL_EVP_DIR}/c_alld.c
                             ${OPENSSL_EVP_DIR}/digest.c
                             ${OPENSSL_EVP_DIR}/e_aes_cbc_hmac_sha1.c
                             ${OPENSSL_EVP_DIR}/e_aes_cbc_hmac_sha256.c
                             ${OPENSSL_EVP_DIR}/e_aes.c
                             ${OPENSSL_EVP_DIR}/e_bf.c
                             ${OPENSSL_EVP_DIR}/e_camellia.c
                             ${OPENSSL_EVP_DIR}/e_cast.c
                             ${OPENSSL_EVP_DIR}/e_des.c
                             ${OPENSSL_EVP_DIR}/e_des3.c
                             #${OPENSSL_EVP_DIR}/e_dsa.c
                             ${OPENSSL_EVP_DIR}/e_idea.c
                             ${OPENSSL_EVP_DIR}/e_null.c
                             ${OPENSSL_EVP_DIR}/e_old.c
                             ${OPENSSL_EVP_DIR}/e_rc2.c
                             ${OPENSSL_EVP_DIR}/e_rc4_hmac_md5.c
                             ${OPENSSL_EVP_DIR}/e_rc4.c
                             ${OPENSSL_EVP_DIR}/e_rc5.c
                             ${OPENSSL_EVP_DIR}/e_seed.c
                             ${OPENSSL_EVP_DIR}/e_xcbc_d.c
                             ${OPENSSL_EVP_DIR}/encode.c
                             ${OPENSSL_EVP_DIR}/evp_acnf.c
                             ${OPENSSL_EVP_DIR}/evp_cnf.c
                             ${OPENSSL_EVP_DIR}/evp_enc.c
                             ${OPENSSL_EVP_DIR}/evp_err.c
                             ${OPENSSL_EVP_DIR}/evp_key.c
                             ${OPENSSL_EVP_DIR}/evp_lib.c
                             ${OPENSSL_EVP_DIR}/evp_locl.h
                             ${OPENSSL_EVP_DIR}/evp_pbe.c
                             ${OPENSSL_EVP_DIR}/evp_pkey.c
                             ${OPENSSL_EVP_DIR}/evp.h
                             ${OPENSSL_EVP_DIR}/m_dss.c
                             ${OPENSSL_EVP_DIR}/m_dss1.c
                             ${OPENSSL_EVP_DIR}/m_ecdsa.c
                             ${OPENSSL_EVP_DIR}/m_md2.c
                             ${OPENSSL_EVP_DIR}/m_md4.c
                             ${OPENSSL_EVP_DIR}/m_md5.c
                             ${OPENSSL_EVP_DIR}/m_mdc2.c
                             ${OPENSSL_EVP_DIR}/m_null.c
                             ${OPENSSL_EVP_DIR}/m_ripemd.c
                             ${OPENSSL_EVP_DIR}/m_sha.c
                             ${OPENSSL_EVP_DIR}/m_sha1.c
                             ${OPENSSL_EVP_DIR}/m_sigver.c
                             ${OPENSSL_EVP_DIR}/m_wp.c
                             ${OPENSSL_EVP_DIR}/names.c
                             ${OPENSSL_EVP_DIR}/openbsd_hw.c
                             ${OPENSSL_EVP_DIR}/p_dec.c
                             ${OPENSSL_EVP_DIR}/p_enc.c
                             ${OPENSSL_EVP_DIR}/p_lib.c
                             ${OPENSSL_EVP_DIR}/p_open.c
                             ${OPENSSL_EVP_DIR}/p_seal.c
                             ${OPENSSL_EVP_DIR}/p_sign.c
                             ${OPENSSL_EVP_DIR}/p_verify.c
                             ${OPENSSL_EVP_DIR}/p5_crpt.c
                             ${OPENSSL_EVP_DIR}/p5_crpt2.c
                             ${OPENSSL_EVP_DIR}/pmeth_fn.c
                             ${OPENSSL_EVP_DIR}/pmeth_gn.c
                             ${OPENSSL_EVP_DIR}/pmeth_lib.c
                             ${OPENSSL_BF_DIR}/bf_cfb64.c
                             ${OPENSSL_BF_DIR}/bf_ecb.c
                             ${OPENSSL_BF_DIR}/bf_enc.c
                             ${OPENSSL_BF_DIR}/bf_locl.h
                             ${OPENSSL_BF_DIR}/bf_ofb64.c
                             ${OPENSSL_BF_DIR}/bf_pi.h
                             ${OPENSSL_BF_DIR}/bf_skey.c
                             ${OPENSSL_BF_DIR}/blowfish.h
                             ${OPENSSL_CAST_DIR}/c_cfb64.c
                             ${OPENSSL_CAST_DIR}/c_ecb.c
                             ${OPENSSL_CAST_DIR}/c_enc.c
                             ${OPENSSL_CAST_DIR}/c_ofb64.c
                             ${OPENSSL_CAST_DIR}/c_skey.c
                             ${OPENSSL_CAST_DIR}/cast_lcl.h
                             ${OPENSSL_CAST_DIR}/cast_s.h
                             ${OPENSSL_CAST_DIR}/cast.h
                             ${OPENSSL_CAMELLIA_DIR}/camellia.c
                             ${OPENSSL_CAMELLIA_DIR}/camellia.h
                             ${OPENSSL_CAMELLIA_DIR}/cmll_cbc.c
                             ${OPENSSL_CAMELLIA_DIR}/cmll_cfb.c
                             ${OPENSSL_CAMELLIA_DIR}/cmll_ctr.c
                             ${OPENSSL_CAMELLIA_DIR}/cmll_ecb.c
                             ${OPENSSL_CAMELLIA_DIR}/cmll_locl.h
                             ${OPENSSL_CAMELLIA_DIR}/cmll_misc.c
                             ${OPENSSL_CAMELLIA_DIR}/cmll_ofb.c
                             ${OPENSSL_CAMELLIA_DIR}/cmll_utl.c
                             ${OPENSSL_DES_DIR}/cbc_cksm.c
                             ${OPENSSL_DES_DIR}/cbc_enc.c
                             ${OPENSSL_DES_DIR}/cbc3_enc.c
                             ${OPENSSL_DES_DIR}/cfb_enc.c
                             ${OPENSSL_DES_DIR}/cfb64ede.c
                             ${OPENSSL_DES_DIR}/cfb64enc.c
                             ${OPENSSL_DES_DIR}/des_enc.c
                             ${OPENSSL_DES_DIR}/des_locl.h
                             ${OPENSSL_DES_DIR}/des_old.c
                             ${OPENSSL_DES_DIR}/des_old.h
                             ${OPENSSL_DES_DIR}/des_old2.c
                             ${OPENSSL_DES_DIR}/des_ver.h
                             ${OPENSSL_DES_DIR}/des.c
                             ${OPENSSL_DES_DIR}/des.h
                             ${OPENSSL_DES_DIR}/ecb_enc.c
                             ${OPENSSL_DES_DIR}/ecb3_enc.c
                             ${OPENSSL_DES_DIR}/ede_cbcm_enc.c
                             ${OPENSSL_DES_DIR}/enc_read.c
                             ${OPENSSL_DES_DIR}/enc_writ.c
                             ${OPENSSL_DES_DIR}/fcrypt_b.c
                             ${OPENSSL_DES_DIR}/fcrypt.c
                             ${OPENSSL_DES_DIR}/ncbc_enc.c
                             ${OPENSSL_DES_DIR}/ofb_enc.c
                             ${OPENSSL_DES_DIR}/ofb64ede.c
                             ${OPENSSL_DES_DIR}/ofb64enc.c
                             ${OPENSSL_DES_DIR}/pcbc_enc.c
                             ${OPENSSL_DES_DIR}/qud_cksm.c
                             ${OPENSSL_DES_DIR}/rand_key.c
                             #${OPENSSL_DES_DIR}/read_pwd.c
                             ${OPENSSL_DES_DIR}/read2pwd.c
                             ${OPENSSL_DES_DIR}/rpc_des.h
                             ${OPENSSL_DES_DIR}/rpc_enc.c
                             ${OPENSSL_DES_DIR}/rpw.c
                             ${OPENSSL_DES_DIR}/set_key.c
                             ${OPENSSL_DES_DIR}/spr.h
                             ${OPENSSL_DES_DIR}/str2key.c
                             ${OPENSSL_DES_DIR}/xcbc_enc.c
                             ${OPENSSL_DH_DIR}/dh_ameth.c
                             ${OPENSSL_DH_DIR}/dh_asn1.c
                             ${OPENSSL_DH_DIR}/dh_check.c
                             ${OPENSSL_DH_DIR}/dh_depr.c
                             ${OPENSSL_DH_DIR}/dh_err.c
                             ${OPENSSL_DH_DIR}/dh_gen.c
                             ${OPENSSL_DH_DIR}/dh_kdf.c
                             ${OPENSSL_DH_DIR}/dh_key.c
                             ${OPENSSL_DH_DIR}/dh_lib.c
                             ${OPENSSL_DH_DIR}/dh_pmeth.c
                             ${OPENSSL_DH_DIR}/dh_prn.c
                             ${OPENSSL_DH_DIR}/dh.h
                             ${OPENSSL_DH_DIR}/dh_rfc5114.c
                             ${OPENSSL_DSA_DIR}/dsa_ameth.c
                             ${OPENSSL_DSA_DIR}/dsa_asn1.c
                             ${OPENSSL_DSA_DIR}/dsa_depr.c
                             ${OPENSSL_DSA_DIR}/dsa_err.c
                             ${OPENSSL_DSA_DIR}/dsa_gen.c
                             ${OPENSSL_DSA_DIR}/dsa_key.c
                             ${OPENSSL_DSA_DIR}/dsa_lib.c
                             ${OPENSSL_DSA_DIR}/dsa_locl.h
                             ${OPENSSL_DSA_DIR}/dsa_ossl.c
                             ${OPENSSL_DSA_DIR}/dsa_pmeth.c
                             ${OPENSSL_DSA_DIR}/dsa_prn.c
                             ${OPENSSL_DSA_DIR}/dsa_sign.c
                             ${OPENSSL_DSA_DIR}/dsa_vrf.c
                             ${OPENSSL_DSA_DIR}/dsa.h
                             ${OPENSSL_ECDSA_DIR}/ecdsa.h
                             ${OPENSSL_ECDSA_DIR}/ecs_asn1.c
                             ${OPENSSL_ECDSA_DIR}/ecs_err.c
                             ${OPENSSL_ECDSA_DIR}/ecs_lib.c
                             ${OPENSSL_ECDSA_DIR}/ecs_locl.h
                             ${OPENSSL_ECDSA_DIR}/ecs_ossl.c
                             ${OPENSSL_ECDSA_DIR}/ecs_sign.c
                             ${OPENSSL_ECDSA_DIR}/ecs_vrf.c
                             ${OPENSSL_EC_DIR}/ec_ameth.c
                             ${OPENSSL_EC_DIR}/ec_asn1.c
                             ${OPENSSL_EC_DIR}/ec_check.c
                             ${OPENSSL_EC_DIR}/ec_curve.c
                             ${OPENSSL_EC_DIR}/ec_cvt.c
                             ${OPENSSL_EC_DIR}/ec_err.c
                             ${OPENSSL_EC_DIR}/ec_key.c
                             ${OPENSSL_EC_DIR}/ec_lcl.h
                             ${OPENSSL_EC_DIR}/ec_lib.c
                             ${OPENSSL_EC_DIR}/ec_mult.c
                             ${OPENSSL_EC_DIR}/ec_oct.c
                             ${OPENSSL_EC_DIR}/ec_pmeth.c
                             ${OPENSSL_EC_DIR}/ec_print.c
                             ${OPENSSL_EC_DIR}/ec.h
                             ${OPENSSL_EC_DIR}/ec2_mult.c
                             ${OPENSSL_EC_DIR}/ec2_oct.c
                             ${OPENSSL_EC_DIR}/ec2_smpl.c
                             ${OPENSSL_EC_DIR}/eck_prn.c
                             ${OPENSSL_EC_DIR}/ecp_mont.c
                             ${OPENSSL_EC_DIR}/ecp_nist.c
                             ${OPENSSL_EC_DIR}/ecp_nistp224.c
                             ${OPENSSL_EC_DIR}/ecp_nistp256.c
                             ${OPENSSL_EC_DIR}/ecp_nistp521.c
                             ${OPENSSL_EC_DIR}/ecp_nistputil.c
                             #${OPENSSL_EC_DIR}/ecp_nistz256_table.c
                             ${OPENSSL_EC_DIR}/ecp_oct.c
                             ${OPENSSL_EC_DIR}/ecp_smpl.c
                             ${OPENSSL_ECDH_DIR}/ecdh.h
                             ${OPENSSL_ECDH_DIR}/ech_err.c
                             ${OPENSSL_ECDH_DIR}/ech_kdf.c
                             ${OPENSSL_ECDH_DIR}/ech_key.c
                             ${OPENSSL_ECDH_DIR}/ech_lib.c
                             ${OPENSSL_ECDH_DIR}/ech_locl.h
                             ${OPENSSL_ECDH_DIR}/ech_ossl.c
                             ${OPENSSL_COMP_DIR}/c_rle.c
                             ${OPENSSL_COMP_DIR}/c_zlib.c
                             ${OPENSSL_COMP_DIR}/comp_err.c
                             ${OPENSSL_COMP_DIR}/comp_lib.c
                             ${OPENSSL_COMP_DIR}/comp.h
                             ${OPENSSL_OBJECTS_DIR}/o_names.c
                             ${OPENSSL_OBJECTS_DIR}/obj_dat.c
                             ${OPENSSL_OBJECTS_DIR}/obj_dat.h
                             ${OPENSSL_OBJECTS_DIR}/obj_err.c
                             ${OPENSSL_OBJECTS_DIR}/obj_lib.c
                             ${OPENSSL_OBJECTS_DIR}/obj_mac.h
                             ${OPENSSL_OBJECTS_DIR}/obj_xref.c
                             ${OPENSSL_OBJECTS_DIR}/obj_xref.h
                             ${OPENSSL_OBJECTS_DIR}/objects.h
                             ${OPENSSL_OCSP_DIR}/ocsp_asn.c
                             ${OPENSSL_OCSP_DIR}/ocsp_cl.c
                             ${OPENSSL_OCSP_DIR}/ocsp_err.c
                             ${OPENSSL_OCSP_DIR}/ocsp_ext.c
                             ${OPENSSL_OCSP_DIR}/ocsp_ht.c
                             ${OPENSSL_OCSP_DIR}/ocsp_lib.c
                             ${OPENSSL_OCSP_DIR}/ocsp_prn.c
                             ${OPENSSL_OCSP_DIR}/ocsp_srv.c
                             ${OPENSSL_OCSP_DIR}/ocsp_vfy.c
                             ${OPENSSL_OCSP_DIR}/ocsp.h
                             ${OPENSSL_PEM_DIR}/pem_all.c
                             ${OPENSSL_PEM_DIR}/pem_err.c
                             ${OPENSSL_PEM_DIR}/pem_info.c
                             ${OPENSSL_PEM_DIR}/pem_lib.c
                             ${OPENSSL_PEM_DIR}/pem_oth.c
                             ${OPENSSL_PEM_DIR}/pem_pk8.c
                             ${OPENSSL_PEM_DIR}/pem_pkey.c
                             ${OPENSSL_PEM_DIR}/pem_seal.c
                             ${OPENSSL_PEM_DIR}/pem_sign.c
                             ${OPENSSL_PEM_DIR}/pem_x509.c
                             ${OPENSSL_PEM_DIR}/pem_xaux.c
                             ${OPENSSL_PEM_DIR}/pem.h
                             ${OPENSSL_PEM_DIR}/pem2.h
                             ${OPENSSL_PEM_DIR}/pvkfmt.c
                             ${OPENSSL_PKCS12_DIR}/p12_add.c
                             ${OPENSSL_PKCS12_DIR}/p12_asn.c
                             ${OPENSSL_PKCS12_DIR}/p12_attr.c
                             ${OPENSSL_PKCS12_DIR}/p12_crpt.c
                             ${OPENSSL_PKCS12_DIR}/p12_crt.c
                             ${OPENSSL_PKCS12_DIR}/p12_decr.c
                             ${OPENSSL_PKCS12_DIR}/p12_init.c
                             ${OPENSSL_PKCS12_DIR}/p12_key.c
                             ${OPENSSL_PKCS12_DIR}/p12_kiss.c
                             ${OPENSSL_PKCS12_DIR}/p12_mutl.c
                             ${OPENSSL_PKCS12_DIR}/p12_npas.c
                             ${OPENSSL_PKCS12_DIR}/p12_p8d.c
                             ${OPENSSL_PKCS12_DIR}/p12_p8e.c
                             ${OPENSSL_PKCS12_DIR}/p12_utl.c
                             ${OPENSSL_PKCS12_DIR}/pk12err.c
                             ${OPENSSL_PKCS12_DIR}/pkcs12.h
                             ${OPENSSL_PKCS7_DIR}/bio_pk7.c
                             ${OPENSSL_PKCS7_DIR}/pk7_asn1.c
                             ${OPENSSL_PKCS7_DIR}/pk7_attr.c
                             ${OPENSSL_PKCS7_DIR}/pk7_dgst.c
                             ${OPENSSL_PKCS7_DIR}/pk7_doit.c
                             #${OPENSSL_PKCS7_DIR}/pk7_enc.c
                             ${OPENSSL_PKCS7_DIR}/pk7_lib.c
                             ${OPENSSL_PKCS7_DIR}/pk7_mime.c
                             ${OPENSSL_PKCS7_DIR}/pk7_smime.c
                             ${OPENSSL_PKCS7_DIR}/pkcs7.h
                             ${OPENSSL_PKCS7_DIR}/pkcs7err.c
                             ${OPENSSL_RAND_DIR}/md_rand.c
                             ${OPENSSL_RAND_DIR}/rand_egd.c
                             ${OPENSSL_RAND_DIR}/rand_err.c
                             ${OPENSSL_RAND_DIR}/rand_lcl.h
                             ${OPENSSL_RAND_DIR}/rand_lib.c
                             ${OPENSSL_RAND_DIR}/rand_nw.c
                             ${OPENSSL_RAND_DIR}/rand_os2.c
                             ${OPENSSL_RAND_DIR}/rand_unix.c
                             ${OPENSSL_RAND_DIR}/rand_vms.c
                             ${OPENSSL_RAND_DIR}/rand_win.c
                             ${OPENSSL_RAND_DIR}/rand.h
                             ${OPENSSL_RAND_DIR}/randfile.c
                             ${OPENSSL_TS_DIR}/ts_asn1.c
                             ${OPENSSL_TS_DIR}/ts_conf.c
                             ${OPENSSL_TS_DIR}/ts_err.c
                             ${OPENSSL_TS_DIR}/ts_lib.c
                             ${OPENSSL_TS_DIR}/ts_req_print.c
                             ${OPENSSL_TS_DIR}/ts_req_utils.c
                             ${OPENSSL_TS_DIR}/ts_rsp_print.c
                             ${OPENSSL_TS_DIR}/ts_rsp_sign.c
                             ${OPENSSL_TS_DIR}/ts_rsp_utils.c
                             ${OPENSSL_TS_DIR}/ts_rsp_verify.c
                             ${OPENSSL_TS_DIR}/ts_verify_ctx.c
                             ${OPENSSL_TS_DIR}/ts.h
                             ${OPENSSL_UI_DIR}/ui_compat.c
                             ${OPENSSL_UI_DIR}/ui_compat.h
                             ${OPENSSL_UI_DIR}/ui_err.c
                             ${OPENSSL_UI_DIR}/ui_lib.c
                             ${OPENSSL_UI_DIR}/ui_locl.h
                             ${OPENSSL_UI_DIR}/ui_openssl.c
                             ${OPENSSL_UI_DIR}/ui_util.c
                             ${OPENSSL_UI_DIR}/ui.h
                             ${OPENSSL_HMAC_DIR}/hm_ameth.c
                             ${OPENSSL_HMAC_DIR}/hm_pmeth.c
                             ${OPENSSL_HMAC_DIR}/hmac.c
                             ${OPENSSL_HMAC_DIR}/hmac.h
                             ${OPENSSL_MD4_DIR}/md4_dgst.c
                             ${OPENSSL_MD4_DIR}/md4_locl.h
                             ${OPENSSL_MD4_DIR}/md4_one.c
                             ${OPENSSL_MD4_DIR}/md4.c
                             ${OPENSSL_MD4_DIR}/md4.h
                             ${OPENSSL_MD5_DIR}/md5_dgst.c
                             ${OPENSSL_MD5_DIR}/md5_locl.h
                             ${OPENSSL_MD5_DIR}/md5_one.c
                             ${OPENSSL_MD5_DIR}/md5.c
                             ${OPENSSL_MD5_DIR}/md5.h
                             ${OPENSSL_MDC2_DIR}/mdc2_one.c
                             ${OPENSSL_MDC2_DIR}/mdc2.h
                             ${OPENSSL_MDC2_DIR}/mdc2dgst.c
                             ${OPENSSL_RC2_DIR}/rc2_cbc.c
                             ${OPENSSL_RC2_DIR}/rc2_ecb.c
                             ${OPENSSL_RC2_DIR}/rc2_locl.h
                             ${OPENSSL_RC2_DIR}/rc2_skey.c
                             ${OPENSSL_RC2_DIR}/rc2.h
                             ${OPENSSL_RC2_DIR}/rc2cfb64.c
                             ${OPENSSL_RC2_DIR}/rc2ofb64.c
                             ${OPENSSL_RC4_DIR}/rc4_enc.c
                             ${OPENSSL_RC4_DIR}/rc4_locl.h
                             ${OPENSSL_RC4_DIR}/rc4_skey.c
                             ${OPENSSL_RC4_DIR}/rc4_utl.c
                             ${OPENSSL_RC4_DIR}/rc4.h
                             ${OPENSSL_RIPEMD_DIR}/ripemd.h
                             ${OPENSSL_RIPEMD_DIR}/rmd_dgst.c
                             ${OPENSSL_RIPEMD_DIR}/rmd_locl.h
                             ${OPENSSL_RIPEMD_DIR}/rmd_one.c
                             ${OPENSSL_RIPEMD_DIR}/rmd160.c
                             ${OPENSSL_RIPEMD_DIR}/rmdconst.h
                             ${OPENSSL_SEED_DIR}/seed_cbc.c
                             ${OPENSSL_SEED_DIR}/seed_cfb.c
                             ${OPENSSL_SEED_DIR}/seed_ecb.c
                             ${OPENSSL_SEED_DIR}/seed_locl.h
                             ${OPENSSL_SEED_DIR}/seed_ofb.c
                             ${OPENSSL_SEED_DIR}/seed.c
                             ${OPENSSL_SEED_DIR}/seed.h
                             ${OPENSSL_SHA_DIR}/sha_dgst.c
                             ${OPENSSL_SHA_DIR}/sha_locl.h
                             ${OPENSSL_SHA_DIR}/sha_one.c
                             ${OPENSSL_SHA_DIR}/sha.c
                             ${OPENSSL_SHA_DIR}/sha.h
                             ${OPENSSL_SHA_DIR}/sha1_one.c
                             ${OPENSSL_SHA_DIR}/sha1.c
                             ${OPENSSL_SHA_DIR}/sha1dgst.c
                             ${OPENSSL_SHA_DIR}/sha256.c
                             ${OPENSSL_SHA_DIR}/sha256t.c
                             ${OPENSSL_SHA_DIR}/sha512.c
                             ${OPENSSL_SHA_DIR}/sha512t.c
                             ${OPENSSL_SRP_DIR}/srp_grps.h
                             ${OPENSSL_SRP_DIR}/srp_lcl.h
                             ${OPENSSL_SRP_DIR}/srp_lib.c
                             ${OPENSSL_SRP_DIR}/srp_vfy.c
                             ${OPENSSL_SRP_DIR}/srp.h
                             ${OPENSSL_TXT_DB_DIR}/txt_db.c
                             ${OPENSSL_TXT_DB_DIR}/txt_db.h
                             ${OPENSSL_WHRLPOOL_DIR}/whrlpool.h
                             ${OPENSSL_WHRLPOOL_DIR}/wp_block.c
                             ${OPENSSL_WHRLPOOL_DIR}/wp_dgst.c
                             ${OPENSSL_WHRLPOOL_DIR}/wp_locl.h
                             ${OPENSSL_IDEA_DIR}/i_cbc.c
                             ${OPENSSL_IDEA_DIR}/i_cfb64.c
                             ${OPENSSL_IDEA_DIR}/i_ecb.c
                             ${OPENSSL_IDEA_DIR}/i_ofb64.c
                             ${OPENSSL_IDEA_DIR}/i_skey.c
                             ${OPENSSL_IDEA_DIR}/idea_lcl.h
                             ${OPENSSL_IDEA_DIR}/idea.h
                             ${OPENSSL_LHASH_DIR}/lh_stats.c
                             ${OPENSSL_LHASH_DIR}/lhash.c
                             ${OPENSSL_LHASH_DIR}/lhash.h
                             ${OPENSSL_PQUEUE_DIR}/pqueue.c
                             ${OPENSSL_PQUEUE_DIR}/pqueue.h
                             ${OPENSSL_STACK_DIR}/safestack.h
                             ${OPENSSL_STACK_DIR}/stack.c
                             ${OPENSSL_STACK_DIR}/stack.h
                             ${OPENSSL_SSL_DIR}/bio_ssl.c
                             ${OPENSSL_SSL_DIR}/d1_both.c
                             ${OPENSSL_SSL_DIR}/d1_clnt.c
                             ${OPENSSL_SSL_DIR}/d1_lib.c
                             ${OPENSSL_SSL_DIR}/d1_meth.c
                             ${OPENSSL_SSL_DIR}/d1_pkt.c
                             ${OPENSSL_SSL_DIR}/d1_srtp.c
                             ${OPENSSL_SSL_DIR}/d1_srvr.c
                             ${OPENSSL_SSL_DIR}/dtls1.h
                             ${OPENSSL_SSL_DIR}/kssl_lcl.h
                             ${OPENSSL_SSL_DIR}/kssl.c
                             ${OPENSSL_SSL_DIR}/kssl.h
                             ${OPENSSL_SSL_DIR}/s2_clnt.c
                             ${OPENSSL_SSL_DIR}/s2_enc.c
                             ${OPENSSL_SSL_DIR}/s2_lib.c
                             ${OPENSSL_SSL_DIR}/s2_meth.c
                             ${OPENSSL_SSL_DIR}/s2_pkt.c
                             ${OPENSSL_SSL_DIR}/s2_srvr.c
                             ${OPENSSL_SSL_DIR}/s3_both.c
                             ${OPENSSL_SSL_DIR}/s3_cbc.c
                             ${OPENSSL_SSL_DIR}/s3_clnt.c
                             ${OPENSSL_SSL_DIR}/s3_enc.c
                             ${OPENSSL_SSL_DIR}/s3_lib.c
                             ${OPENSSL_SSL_DIR}/s3_meth.c
                             ${OPENSSL_SSL_DIR}/s3_pkt.c
                             ${OPENSSL_SSL_DIR}/s3_srvr.c
                             ${OPENSSL_SSL_DIR}/s23_clnt.c
                             ${OPENSSL_SSL_DIR}/s23_lib.c
                             ${OPENSSL_SSL_DIR}/s23_meth.c
                             ${OPENSSL_SSL_DIR}/s23_pkt.c
                             ${OPENSSL_SSL_DIR}/s23_srvr.c
                             ${OPENSSL_SSL_DIR}/srtp.h
                             ${OPENSSL_SSL_DIR}/ssl_algs.c
                             ${OPENSSL_SSL_DIR}/ssl_asn1.c
                             ${OPENSSL_SSL_DIR}/ssl_cert.c
                             ${OPENSSL_SSL_DIR}/ssl_ciph.c
                             ${OPENSSL_SSL_DIR}/ssl_conf.c
                             ${OPENSSL_SSL_DIR}/ssl_err.c
                             ${OPENSSL_SSL_DIR}/ssl_err2.c
                             ${OPENSSL_SSL_DIR}/ssl_lib.c
                             ${OPENSSL_SSL_DIR}/ssl_locl.h
                             ${OPENSSL_SSL_DIR}/ssl_rsa.c
                             ${OPENSSL_SSL_DIR}/ssl_sess.c
                             ${OPENSSL_SSL_DIR}/ssl_stat.c
                             ${OPENSSL_SSL_DIR}/ssl_txt.c
                             ${OPENSSL_SSL_DIR}/ssl_utst.c
                             ${OPENSSL_SSL_DIR}/ssl.h
                             ${OPENSSL_SSL_DIR}/ssl2.h
                             ${OPENSSL_SSL_DIR}/ssl3.h
                             ${OPENSSL_SSL_DIR}/ssl23.h
                             ${OPENSSL_SSL_DIR}/t1_clnt.c
                             ${OPENSSL_SSL_DIR}/t1_enc.c
                             ${OPENSSL_SSL_DIR}/t1_ext.c
                             ${OPENSSL_SSL_DIR}/t1_lib.c
                             ${OPENSSL_SSL_DIR}/t1_meth.c
                             ${OPENSSL_SSL_DIR}/t1_reneg.c
                             ${OPENSSL_SSL_DIR}/t1_srvr.c
                             ${OPENSSL_SSL_DIR}/t1_trce.c
                             ${OPENSSL_SSL_DIR}/tls_srp.c
                             ${OPENSSL_SSL_DIR}/tls1.h)

  set(OPENSSL_CRYPTO_LIBRARY openssl_crypto CACHE STRING "OpenSSL Crypto Library" FORCE)
  set(OPENSSL_SSL_LIBRARY openssl CACHE STRING "OpenSSL SSL Library" FORCE)
  set_target_properties(openssl_crypto openssl
      PROPERTIES
      ARCHIVE_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/openssl/lib"
      ARCHIVE_OUTPUT_DIRECTORY_DEBUG "${CMAKE_BINARY_DIR}/openssl/lib/Debug"
      ARCHIVE_OUTPUT_DIRECTORY_RELEASE "${CMAKE_BINARY_DIR}/openssl/lib/Release"
      LIBRARY_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/openssl/lib"
      LIBRARY_OUTPUT_DIRECTORY_DEBUG "${CMAKE_BINARY_DIR}/openssl/lib/Debug"
      LIBRARY_OUTPUT_DIRECTORY_RELEASE "${CMAKE_BINARY_DIR}/openssl/lib/Release"
  )
  set(OPENSSL_ROOT_DIR "${CMAKE_BINARY_DIR}/openssl" CACHE STRING "OpenSSL Root Directory" FORCE)
  target_include_directories(openssl PUBLIC ${OPENSSL_INCLUDE_DIR})
  target_include_directories(openssl PRIVATE ${OPENSSL_CRYPTO_DIR}
                                             ${OPENSSL_DIR}
                                             ${OPENSSL_ASN1_DIR}
                                             ${OPENSSL_EVP_DIR}
                                             ${OPENSSL_MODES_DIR})
  target_include_directories(openssl_crypto PRIVATE ${OPENSSL_CRYPTO_DIR}
                                                    ${OPENSSL_DIR}
                                                    ${OPENSSL_ASN1_DIR}
                                                    ${OPENSSL_EVP_DIR}
                                                    ${OPENSSL_MODES_DIR})
  target_include_directories(openssl_crypto PUBLIC ${OPENSSL_INCLUDE_DIR})
  target_link_libraries(openssl PUBLIC ${OPENSSL_CRYPTO_LIBRARY})
  set(OPENSSL_LIBRARIES "${OPENSSL_SSL_LIBRARY};${OPENSSL_CRYPTO_LIBRARY}" CACHE INTERNAL "OpenSSL Libraries" FORCE)
  set(OPENSSL_INSTALL_CMAKE_DIR lib/cmake/openssl)
  if(ANDROID)
    target_compile_definitions(openssl PRIVATE TIMES=1)
  endif()
else()
  message(STATUS "OpenSSL found on system")
endif()


# Add json
set(JSON_BuildTests OFF CACHE BOOL "Don't build JSON tests" FORCE)
add_subdirectory(json)

# Conditionally add curl
if(USE_CURL)
  set(CMAKE_DEBUG_POSTFIX "" CACHE STRING "Override CMAKE_DEBUG_POSTFIX, which curl sets to '-d'")
  set(BUILD_TESTING OFF CACHE BOOL "Don't build curl tests" FORCE)
  set(BUILD_CURL_EXE OFF CACHE BOOL "Don't build curl executables" FORCE)
  set(CURL_STATICLIB ON CACHE BOOL "Build the curl static library" FORCE)
  set(CURL_DISABLE_LDAP ON CACHE BOOL "Disable ldap" FORCE)
  set(CURL_CA_FALLBACK ON CACHE BOOL "Use built-in CA" FORCE)
  set(CURL_INSTALL OFF CACHE BOOL "Don't allow cURL to install" FORCE)
  # Android does not support fsetxattr
  if(ANDROID)
   set(HAVE_FSETXATTR OFF CACHE BOOL "We do not have fsetxattr" FORCE)
    set(HAVE_GLIBC_STRERROR_R OFF CACHE BOOL "We do not have glibc strerror" FORCE)
    set(HAVE_GLIBC_STRERROR_R__TRYRUN_OUTPUT "" CACHE STRING "Force the strerror output" FORCE)
    set(HAVE_POSIX_STRERROR_R ON CACHE BOOL "We do have posix strerror" FORCE)
    set(HAVE_POSIX_STRERROR_R__TRYRUN_OUTPUT "" CACHE STRING "Force the posix strerror output" FORCE)
    set(HAVE_POLL_FINE_EXITCODE "0" CACHE STRING "Force poll fine exit code" FORCE)
  endif()
  add_subdirectory(curl EXCLUDE_FROM_ALL)
endif()

# Conditionally add Microsoft's C++ Rest SDK
if(USE_CPPRESTSDK)
  set(CPPREST_INCLUDE_DIR "${CMAKE_CURRENT_SOURCE_DIR}/cpprestsdk/Release/include" CACHE STRING "C++ REST SDK Includes" FORCE)
  set(BOOST_LIBRARYDIR ${BOOST_LIB_DIR})
  set(CPPREST_INSTALL OFF CACHE BOOL "Don't install" FORCE)
  set(CPPREST_INSTALL_HEADERS OFF CACHE BOOL "Don't install headers" FORCE)
  set(BUILD_SHARED_LIBS OFF CACHE BOOL "Build cpprest as a static lib" FORCE)
  set(CPPREST_EXCLUDE_COMPRESSION ON CACHE BOOL "Exclude compression functionality." FORCE)
  add_definitions(-DSSL_R_SHORT_READ)
  add_subdirectory(cpprestsdk/Release)
endif()
