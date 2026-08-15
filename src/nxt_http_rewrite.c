
/*
 * Copyright (C) Zhidao HONG
 * Copyright (C) NGINX, Inc.
 */

#include <nxt_router.h>
#include <nxt_http.h>


nxt_int_t
nxt_http_rewrite_init(nxt_router_conf_t *rtcf, nxt_http_action_t *action,
     nxt_http_action_conf_t *acf)
 {
    nxt_str_t  str, *rewrite;

    nxt_conf_get_string(acf->rewrite, &str);

    rewrite = nxt_str_dup(rtcf->mem_pool, NULL, &str);
    if (nxt_slow_path(rewrite == NULL)) {
        return NXT_ERROR;
    }

    action->rewrite = rewrite;

    return NXT_OK;
}


nxt_int_t
nxt_http_rewrite(nxt_task_t *task, nxt_http_request_t *r)
{
    u_char                    *p;
    nxt_int_t                 ret;
    nxt_str_t                 str, encoded_path, target;
    nxt_http_action_t         *action;
    nxt_http_request_parse_t  rp;

    action = r->action;

    if (action == NULL || action->rewrite == NULL) {
        return NXT_OK;
    }

    str = *action->rewrite;

    nxt_memzero(&rp, sizeof(nxt_http_request_parse_t));

    rp.mem_pool = r->mem_pool;

    rp.target_start = str.start;
    rp.target_end = str.start + str.length;

    ret = nxt_http_parse_complex_target(&rp);
    if (nxt_slow_path(ret != NXT_OK)) {
        return NXT_ERROR;
    }

    p = (rp.args.length > 0) ? rp.args.start - 1 : rp.target_end;

    encoded_path.start = rp.target_start;
    encoded_path.length = p - encoded_path.start;

    if (r->original_target.start == NULL) {
        r->original_target = r->target;
    }

    if (r->args->length == 0) {
        r->target = encoded_path;

    } else {
        target.length = encoded_path.length + 1 + r->args->length;

        target.start = nxt_mp_alloc(r->mem_pool, target.length);
        if (target.start == NULL) {
            return NXT_ERROR;
        }

        p = nxt_cpymem(target.start, encoded_path.start, encoded_path.length);
        *p++ = '?';
        nxt_memcpy(p, r->args->start, r->args->length);

        r->target = target;
        r->args->start = p;
    }

    r->path = nxt_mp_alloc(r->mem_pool, sizeof(nxt_str_t));
    if (nxt_slow_path(r->path == NULL)) {
        return NXT_ERROR;
    }

    *r->path = rp.path;

    r->uri_changed = 1;
    r->quoted_target = rp.quoted_target;

    return NXT_OK;
}
