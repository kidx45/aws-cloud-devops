### Week 2: Networking & IAM Fundamentals

#### CheckList

- [x] README.md — answers, calculations, command results, and explanations.
- [x] s3-read-policy.json — completed IAM policy.
- [x] evidence/ — screenshots showing relevant command output or work.

#### Identify Your Network Information

- **Operating System**: [EndeavourOS x86_64]
- **Local IPv4 address**: [10.197.82.204/24]
- **Default Gateway**: [10.197.82.209]
- **Is private or public**: [It is a private IP address]

#### Practice Subnetting

- **Original IP**: [10.0.0.0/24]
*Since we require want 4 sub-networks, will first try to find the number of bits we want to borrow hence 2^x = 4 which will result in 2*

- **Bits to borrow**: 2
- **New prefix**: /24 + 2 = /26
- **New Host Bits**: 32 - 26 = 6
- **Number of addresses in each sub-network (CIDR)** : 64

| | Subnet-1 | Subnet-2 | Subnet-3 | Subnet-4 |
| --------------- | --------------- | --------------- | --------------- | --------------- |
| Network Address | 10.0.0.0 | 10.0.0.64 | 10.0.0.128 | 10.0.0.192 |
| Full Address Range | .0 - .63 | .64 - .127 | .128 - .191 | .192 - .255 |
| Usable Address Range | .1 - .62 | .65 - .126 | .129 - .190 | .193 - .254 |
| Broadcast Address | 10.0.0.63 | 10.0.0.127 | 10.0.0.191 | 10.0.0.255 |

- **Number of usabe address according to AWS VPC rule for each sub-network**: 64 - 5 = 59

#### Test DNS Resolution

- **The domain name tested:** example.com
- **Whether DNS resolution succeeded:** Yes, it succeeded.
- **One or more IP addresses returned:**
  - `172.66.147.243` (IPv4)
  - `104.20.23.154` (IPv4)
  - `2606:4700:10::ac42:93f3` (IPv6)
  - `2606:4700:10::6814:179a` (IPv6)
- **What DNS does, in your own words:** DNS acts like a translater to translate human-readable domain names such as example.com into computer-readable IP addresses (like `172.66.147.243`) so browsers can locate and load websites.

#### Inspect an HTTPS Website

- **Has the website loaded**: Yes, the website has loaded successfully
- **Returned HTTP status code**: [200]
- **What does HTTPS add over HTTP**: HTTPS adds an encryption layer (called SSL/TLS) over standard HTTP. This layer encrypts the data being transmitted between the user's browser and the website server. Because the data is unreadable text to outsiders, it prevents attackers from reading or altering sensitive information like passwords or credit card numbers, while it is traveling across the network.
- DNS resolution alone does not guarantee a website will load because it only converts a domain name into an IP address. Hence website not loading might also be the result of:
  - The hosting server might be entirely powered down, crashing, or experiencing heavy traffic or software misconfigurations (such as 500 Internal Server Errors).
  - There may be local network drops, faulty routing, or internet service provider (ISP) outages between your device and the destination server.
  - Firewalls, corporate network blocks, or local antivirus settings on your machine might intercept and block traffic to that specific IP address.

#### Interpret HTTP Status Codes

| Status Code | Meaning | Example |
| --------------- | --------------- | --------------- |
| 200 | Success | When requesting for a website or curl a URL successfully |
| 301 | Permanently Redirected | When click an ads or a link redirecting to another tab |
| 403 | Unauthorized | When the user doesn't have the privlage to access certain section of the website |
| 404 | Page not found | When requesting for an endpoint that isn't set by router |
| 500 | Internal Server | When server fails internal due to say loss of connection with the database engine |

- What are the difference

| | Column2 | Column3 |
| --------------- | --------------- | --------------- |
| DNS Failure | No Connection | Due to wrong domain name or DNS provider |
| Connection Timeout | Maybe but it will be silent | Due to server outage, network issue or strict firewall |
| TLS Certificate Error | Connects but aborts | Due to the certificate not being authentic |
| HTTP Response Error | Connects to server but can't access service | Due to user not being authenticated properly .. |

#### Write a Least-Privilege IAM Policy

- **Which field specifies the permitted action**: The "Action" field specifies the specific API operations allowed or denied (in this case, `"s3:GetObject"`).

- **Which field specifies the resources**: The "Resource" field specifies the specific AWS assets the policy applies to (in this case, `"arn:aws:s3:::example-bucket/*"`).

- **Does s3:GetObject allow listing all objects in a bucket**: No. `s3:GetObject` only allows a user to download or read the contents of specific files if they already know the path. To list all objects inside a bucket, a separate permission called `s3:ListBucket` is required.

- **Why is a narrow permission safer than granting s3:\***: Granting `s3:*` gives full administrative control over all S3 buckets, allowing an identity to delete buckets, wipe out data, or change public security settings which might lead to a security issues if caught by attackers.

- **Why should AWS access keys never be committed to GitHub**: GitHub repositories are constantly scanned by automated malicious bots. If long-term AWS access keys are committed to a public repository, bots will scrape them within seconds and use them to spin up expensive resources (like crypto-mining servers) or steal private company data, resulting in massive financial bills and severe security breaches.

#### Troubleshooting Practice

| Column1 | Column2 | Column3 |
| --------------- | --------------- | --------------- |
| A domain name does not resolve to an IP address | DNS | DNS is responsible for translation of domain name to IP address hence will be the prime suspect to look into |
| A domain resolves, but the browser connection times out | network connectivity | Connection timeout usually indicate that the browser and server weren't able to connect due to network on either side |
| The browser displays a TLS certificate warning | TLS | TLS certificates ensure the authenticity of a website hence if not accepted by browser, this is usually due the server TLS not being renewed or being the wrong website |
| A website responds with HTTP 404 | HTTP/Application | This occurs due to the HTTP endpoint not existing |
| An EC2 application can reach Amazon S3 but receives AccessDenied when reading an object | IAM/S3 Authorization | In order to limit the allowed actions on s3 buckets, we specify rules and policies which affect accessibility and visiblity of these buckets |
