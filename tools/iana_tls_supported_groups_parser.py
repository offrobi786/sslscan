#!/usr/bin/python3

#
# Copyright (C) 2019  Joe Testa <jtesta@positronsecurity.com>
#
# This tool will parse the list of TLS supported groups from IANA
# (https://www.iana.org/assignments/tls-parameters/tls-parameters-8.csv) into a C-struct
# for use in testSupportedGroups().
#

import csv, sys
from datetime import date


# We must be given a path to a CSV file with the groups.  It can be obtained from
# <https://www.iana.org/assignments/tls-parameters/tls-parameters-8.csv>.
if len(sys.argv) != 2:
    print("\nUsage: %s tls_ciphers.csv\n\nHint: copy the TLS table in CSV format from <https://www.iana.org/assignments/tls-parameters/tls-parameters-8.csv>.\n" % sys.argv[0])
    exit(0)

csv_file = sys.argv[1]

print()
print("  /* Auto-generated by %s on %s. */" % (sys.argv[0], date.today().strftime("%B %d, %Y")))
print('#define COL_PLAIN ""')
print('#define NID_TYPE_NA 0    /* Not Applicable (i.e.: X25519/X448) */')
print('#define NID_TYPE_ECDHE 1 /* For ECDHE curves (sec*, P-256/384-521) */')
print('#define NID_TYPE_DHE 2   /* For ffdhe* */')
print("  /* Bit strength of DHE 2048 and 3072-bit moduli is taken directly from NIST SP 800-57 pt.1, rev4., pg. 53; DHE 4096, 6144, and 8192 are estimated using that document. */")
print("  struct group_key_exchange group_key_exchanges[] = {")
with open(csv_file, 'r') as f:
    reader = csv.reader(f)
    for row in reader:
        id = row[0]
        group_name = row[1]
        reference = row[4]
        
        # Skip the header.
        try:
            int(id)
        except ValueError as e:
            continue

        id = int(id)

        # Skip reserved or unassigned IDs.
        if group_name in ('Reserved', 'Unassigned'):
            continue

        # The Reference field looks like "[RFC1234]", "[draft-blah-blah]", or "[RFC-ietf-tls-blah-02]".  Skip all rows that aren't of the "[RFC1234]" variety.
        reference = reference[1:]
        rt_bracket_pos = reference.find(']')
        if rt_bracket_pos == -1:
            print("Warning: can't parse reference: %s" % reference)
        else:
            reference = reference[3:rt_bracket_pos]

        try:
            int(reference)
        except ValueError as e:
            continue

        bits = 0
        nid = "NID_x"
        nid_type = "NID_TYPE_x"
        key_exchange_len = 0
        color = "COL_PLAIN"
        if group_name.startswith('sec'):
            bits = int(group_name[4:-2]) / 2
            nid = "NID_%s" % group_name
            nid_type = "NID_TYPE_ECDHE"
            if group_name == "secp192r1":
                nid = "NID_X9_62_prime192v1"
            elif group_name == "secp256r1":
                nid = "NID_X9_62_prime256v1"
                group_name += ' (NIST P-256)'
            elif group_name == "secp256k1":
                color = "COL_GREEN"  # This is the very well-tested Bitcoin curve.
            elif group_name == "secp384r1":
                group_name += ' (NIST P-384)'
            elif group_name == "secp521r1":
                group_name += ' (NIST P-521)'
        elif group_name.startswith('brainpoolP'):
            bits = int(group_name[10:-2]) / 2
            nid = "NID_%s" % group_name
            nid_type = "NID_TYPE_ECDHE"
        elif group_name in ('x25519', 'x448'):
            color = "COL_GREEN"
            nid = "-1"
            nid_type = "NID_TYPE_NA"
            if group_name == 'x25519':
                bits = 128
                key_exchange_len = 32
            elif group_name == 'x448':
                bits = 224
                key_exchange_len = 56
        elif group_name.startswith('ffdhe'):
            # Bit strength of DHE 2048 and 3072-bit moduli is taken directly from NIST SP 800-57 pt.1, rev4., pg. 53; DHE 4096, 6144, and 8192 are estimated using that document.
            if group_name == 'ffdhe2048':
                bits = 112
                key_exchange_len = 256
            elif group_name == 'ffdhe3072':
                bits = 128
                key_exchange_len = 384
            elif group_name == 'ffdhe4096':
                bits = 150
                key_exchange_len = 512
            elif group_name == 'ffdhe6144':
                bits = 175
                key_exchange_len = 768
            elif group_name == 'ffdhe8192':
                bits = 192
                key_exchange_len = 1024
            nid = "NID_%s" % group_name
            nid_type = "NID_TYPE_DHE"
        elif group_name.startswith('arbitrary_'): # Skip these two.
            continue

        if bits < 112:
            color = "COL_RED"

        print('    {0x%04x, "%s", %d, %s, %s, %s, %d},' % (id, group_name, bits, color, nid, nid_type, key_exchange_len))

print("  };")
print()
exit(0)
