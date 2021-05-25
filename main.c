#include <esp_wifi.h>
#include <esp_timer.h>
#include <esp_event.h>
#include <net/net_if.h>
#include <net/net_core.h>
#include <net/net_context.h>
#include <net/net_mgmt.h>
#include <sys/printk.h>

static void print_ipv4(const char *label, void *addr)
{
	char buf[NET_IPV4_ADDR_LEN];

	printk("%s: %s\n", label,
	       net_addr_ntop(AF_INET, addr, buf, sizeof(buf)));
}

static void handler_cb(struct net_mgmt_event_callback *cb,
		       uint32_t mgmt_event, struct net_if *iface)
{

	if (mgmt_event != NET_EVENT_IPV4_DHCP_BOUND) {
		return;
	}

	print_ipv4("Address", &iface->config.dhcpv4.requested_ip);
	printk("Lease time: %u seconds", iface->config.dhcpv4.lease_time);
	print_ipv4("Netmask", &iface->config.ip.ipv4->netmask);
	print_ipv4("Gateway", &iface->config.ip.ipv4->gw);
}

void main(void)
{
	static struct net_mgmt_event_callback dhcp_cb;
	struct net_if *iface;

	net_mgmt_init_event_callback(&dhcp_cb, handler_cb,
				     NET_EVENT_IPV4_DHCP_BOUND);
	net_mgmt_add_event_callback(&dhcp_cb);

	iface = net_if_get_default();
	if (!iface) {
		printk("wifi interface not available\n");
		return;
	}

	net_dhcpv4_start(iface);
	printk("Hello world!\n");
}
