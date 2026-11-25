# Network plan

Complete this before you create any resources, and send it to your mentor with your diagram.

- **Region:**
- **VPC CIDR (10.N.0.0/16):**

## Subnets

AWS reserves 5 addresses in every subnet. Show how you worked out each range.

| Subnet | CIDR | Usable range | Usable IPs | AZ | Purpose | Why this size |
|---|---|---|---:|---|---|---|
| public | | | | | | |
| private-a | | | | | | |
| private-b | | | | | | |

## Route tables

| Route table | Routes | Associated subnets |
|---|---|---|
| main | local only | none (left untouched) |
| public-rt | | |
| private-rt | | |

## Questions

Answer each in one or two sentences, in your own words.

1. What is a VPC, and how is it different from a subnet?
2. What does /16 mean?
3. What makes a subnet public?
4. Why do we separate public and private subnets?
5. Why does RDS need a DB subnet group that covers two Availability Zones?
6. Why must the database not be publicly accessible?
