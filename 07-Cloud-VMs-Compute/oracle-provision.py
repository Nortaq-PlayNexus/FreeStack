#!/usr/bin/env python3
"""
oracle-provision.py - provision the Oracle Cloud ALWAYS FREE instance.
Creates VCN, internet gateway, subnet, NSG (ports 22/80/443), and a VM.Standard.A1.Flex
instance (4 OCPU / 24GB, free). Uses the oci CLI (auth via `oci setup config`).

Usage:
    python3 oracle-provision.py --ssh-key ~/.ssh/id_ed25519.pub
    python3 oracle-provision.py --ssh-key ~/.ssh/id_ed25519.pub --ocpu 4 --ram 24
"""
import argparse, os, subprocess, sys, time

DEFAULTS = {
    "ocpu": 4, "ram": 24, "shape": "VM.Standard.A1.Flex",
    "image": "ocid1.image.oc1..aaaaaaaafl4d2x5c4p7flz3g6zq3q4k5n6m7l8k9j0h1g2f3d4s5a6b7c8d",  # placeholder, replaced below
    "ssh_user": "ubuntu",
}


def sh(*args, check=True):
    r = subprocess.run([str(a) for a in args], capture_output=True, text=True)
    if check and r.returncode != 0:
        print(r.stderr or r.stdout)
        sys.exit(1)
    return r.stdout.strip()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ssh-key", required=True)
    ap.add_argument("--ocpu", type=int, default=DEFAULTS["ocpu"])
    ap.add_argument("--ram", type=int, default=DEFAULTS["ram"])
    ap.add_argument("--name", default="freestack")
    args = ap.parse_args()

    if not os.path.exists(args.ssh_key):
        print(f"ssh key not found: {args.ssh_key}")
        return 1

    # 1. compartment (root tenancy compartment)
    comp = sh("oci", "iam", "compartment", "list", "--all") 
    import json
    comp = json.loads(comp)["data"]
    compartment = next((c for c in comp if c["compartment-id"] == c["id"]), comp[0])
    ocid = compartment["id"]
    print(f">> compartment: {compartment['name']}")

    # 2. look up a current Ubuntu 24.04 ARM image
    images = json.loads(sh("oci", "compute", "image", "list",
                           "--compartment-id", ocid, "--operating-system", "Canonical Ubuntu",
                           "--shape", DEFAULTS["shape"], "--all"))
    images = [i for i in images["data"] if "aarch64" in i.get("display-name", "").lower()]
    images.sort(key=lambda i: i.get("time-created", ""), reverse=True)
    if not images:
        print("no matching Ubuntu ARM image found; pick one manually and set DEFAULTS['image']")
        return 1
    image_ocid = images[0]["id"]
    print(f">> image: {images[0]['display-name']}")

    # 3. VCN
    vcn = json.loads(sh("oci", "network", "vcn", "create",
                        "--compartment-id", ocid, "--cidr-block", "10.0.0.0/16",
                        "--display-name", args.name, "--wait-for-state", "AVAILABLE"))
    vcn_id = vcn["data"]["id"]

    # 4. internet gateway
    igw = json.loads(sh("oci", "network", "internet-gateway", "create",
                        "--compartment-id", ocid, "--is-enabled", "true",
                        "--vcn-id", vcn_id, "--display-name", f"{args.name}-igw"))
    igw_id = igw["data"]["id"]

    # 5. route table -> internet
    rt = json.loads(sh("oci", "network", "route-table", "create",
                       "--compartment-id", ocid, "--vcn-id", vcn_id,
                       "--route-rules", json.dumps([{"destination": "0.0.0.0/0", "destinationType": "CIDR_BLOCK", "networkEntityId": igw_id}]),
                       "--display-name", f"{args.name}-rt"))
    rt_id = rt["data"]["id"]

    # 6. subnet
    sub = json.loads(sh("oci", "network", "subnet", "create",
                        "--compartment-id", ocid, "--vcn-id", vcn_id,
                        "--cidr-block", "10.0.0.0/24", "--route-table-id", rt_id,
                        "--display-name", f"{args.name}-sub"))
    subnet_id = sub["data"]["id"]

    # 7. security list: allow 22/80/443 ingress
    sl = json.loads(sh("oci", "network", "security-list", "create",
                       "--compartment-id", ocid, "--vcn-id", vcn_id,
                       "--ingress-security-rules", json.dumps([
                           {"source": "0.0.0.0/0", "protocol": "6", "tcpOptions": {"destinationPortRange": {"min": 22, "max": 22}}},
                           {"source": "0.0.0.0/0", "protocol": "6", "tcpOptions": {"destinationPortRange": {"min": 80, "max": 80}}},
                           {"source": "0.0.0.0/0", "protocol": "6", "tcpOptions": {"destinationPortRange": {"min": 443, "max": 443}}},
                       ]),
                       "--display-name", f"{args.name}-sl"))

    # 8. the free instance (A1 flex capacity is per-AD; try each until one accepts)
    ads = json.loads(sh("oci", "iam", "availability-domain", "list", "--compartment-id", ocid))["data"]
    with open(args.ssh_key) as f:
        pub = f.read().strip()
    instance_id = None
    for ad in ads:
        ad_name = ad["name"]
        print(f">> trying launch in {ad_name}...")
        try:
            inst = json.loads(sh("oci", "compute", "instance", "launch",
                                 "--compartment-id", ocid, "--availability-domain", ad_name,
                                 "--shape", DEFAULTS["shape"],
                                 "--shape-config", json.dumps({"ocpus": args.ocpu, "memoryInGBs": args.ram}),
                                 "--subnet-id", subnet_id, "--image-id", image_ocid,
                                 "--display-name", args.name,
                                 "--metadata", json.dumps({"ssh_authorized_keys": pub})))
            instance_id = inst["data"]["id"]
            break
        except SystemExit:
            print(f"    {ad_name}: out of capacity, trying next...")
    if not instance_id:
        print(">> all ADs out of free capacity right now. Retry in a few hours, or reduce --ocpu/--ram.")
        return 1

    print(f">> instance launched: {instance_id}")
    print(f">> find IP:  oci compute instance list-vnics --instance-id {instance_id} --compartment-id {ocid}")
    print(f">> ssh:      ssh {DEFAULTS['ssh_user']}@<public-ip>  then run bootstrap-server.sh")
    return 0


if __name__ == "__main__":
    sys.exit(main())
