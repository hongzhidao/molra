
/*
 * Copyright (C) NGINX, Inc.
 */

#ifndef _NXT_H1PROTO_H_INCLUDED_
#define _NXT_H1PROTO_H_INCLUDED_


#include <nxt_main.h>
#include <nxt_http_parse.h>
#include <nxt_http.h>
#include <nxt_router.h>


struct nxt_h1proto_s {
    nxt_http_request_parse_t  parser;

    uint8_t                   nbuffers;
    uint8_t                   header_buffer_slot;
    uint8_t                   large_buffer_slot;
    uint8_t                   keepalive;            /* 1 bit  */
    uint8_t                   chunked;              /* 1 bit  */
    nxt_http_te_t             transfer_encoding:8;  /* 2 bits */

    uint32_t                  header_size;

    nxt_http_request_t        *request;
    nxt_buf_t                 *buffers;

    nxt_buf_t                 **conn_write_tail;
    /*
     * All fields before the conn field will
     * be zeroed in a keep-alive connection.
     */
    nxt_conn_t                *conn;
};

#define nxt_h1p_is_http11(h1p)                                              \
    ((h1p)->parser.version.s.minor != '0')

#endif  /* _NXT_H1PROTO_H_INCLUDED_ */
