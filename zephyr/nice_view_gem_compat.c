#include <zmk/endpoints.h>
#include <zmk/endpoints_types.h>

struct zmk_endpoint_instance zmk_endpoints_selected(void) {
#if !defined(CONFIG_ZMK_SPLIT) || defined(CONFIG_ZMK_SPLIT_ROLE_CENTRAL)
    return zmk_endpoint_get_selected();
#else
    return (struct zmk_endpoint_instance){.transport = ZMK_TRANSPORT_NONE};
#endif
}
