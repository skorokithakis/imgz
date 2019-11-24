terraform {
  backend "s3" {
    bucket = "terraformstate.stochastic.io"
    key    = "imgz/terraform.tfstate"
    region = "eu-central-1"
  }
}

variable "cloudflare_email" {}
variable "cloudflare_api_key" {}

variable ipv6_ip { default = "2a01:4f8:1c0c:6109::1" }
variable ipv4_ip { default = "195.201.40.251" }
variable zone { default = "03a5ad171d3bccca251801f877714030" }
variable zone2 { default = "890ecf64925760315d370ec4f0eb3ae8" }

provider "cloudflare" {
  version = "~> 2.0"
  email = "${var.cloudflare_email}"
  api_key = "${var.cloudflare_api_key}"
}

resource "cloudflare_record" "v6_root" {
  zone_id=var.zone
  type="AAAA"
  name="@"
  proxied="true"
  value="${var.ipv6_ip}"
}

resource "cloudflare_record" "v6_www" {
  zone_id=var.zone
  type="AAAA"
  name="www"
  proxied="true"
  value="${var.ipv6_ip}"
}

resource "cloudflare_record" "root" {
  zone_id=var.zone
  type="A"
  name="@"
  proxied="true"
  value="${var.ipv4_ip}"
}

resource "cloudflare_record" "www" {
  zone_id=var.zone
  type="A"
  name="www"
  proxied="true"
  value="${var.ipv4_ip}"
}

resource "cloudflare_record" "mg" {
  zone_id=var.zone
  type="CNAME"
  name="email.mail"
  value="eu.mailgun.org"
}

resource "cloudflare_record" "brave_verification" {
  zone_id=var.zone
  type="TXT"
  name="@"
  value="brave-ledger-verification=95e73833c2e2d140ec37779d3c7ed5890199869a0f53341a859410c26e478f58"
}

resource "cloudflare_record" "spf" {
  zone_id=var.zone
  type="TXT"
  name="mail"
  value="v=spf1 include:eu.mailgun.org ~all"
}

resource "cloudflare_record" "root_spf" {
  zone_id=var.zone
  type="TXT"
  name="@"
  value="v=spf1 include:_spf.elasticemail.com include:eu.mailgun.org ~all"
}

resource "cloudflare_record" "elasticmail_mx_domainkey" {
  zone_id=var.zone
  type="TXT"
  name="api._domainkey"
  value="k=rsa;t=s;p=MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQCbmGbQMzYeMvxwtNQoXN0waGYaciuKx8mtMh5czguT4EZlJXuCt6V+l56mmt3t68FEX5JJ0q4ijG71BGoFRkl87uJi7LrQt1ZZmZCvrEII0YO4mp8sDLXC8g1aUAoi8TJgxq2MJqCaMyj5kAm3Fdy2tzftPCV/lbdiJqmBnWKjtwIDAQAB"
}

resource "cloudflare_record" "tracking" {
  zone_id=var.zone
  type="CNAME"
  name="tracking"
  value="api.elasticemail.com"
}

resource "cloudflare_record" "elasticemail_dmarc" {
  zone_id = var.zone
  name="_dmarc"
  type="TXT"
  value="v=DMARC1;p=none;pct=20;aspf=r;adkim=r;"
}

resource "cloudflare_record" "mx_domainkey" {
  zone_id=var.zone
  type="TXT"
  name="pic._domainkey.mail"
  value="k=rsa; p=MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA6m6Fr5fmS9pVGiKOgEG57MnR/r/FtLaUdG93u7rC+HIiqjeUPMwPx4Aya7TDAE03/p4BQdZ5w3WQpowsLp7tzSnNhVLAe8jiMzCJ610qEO7j/ys5TeI9SPt1nGaccLbhCcawz3T0KKV4sHrKxsZOnayDuuj3QMhVJn4AbzX7JYrbrg3NfP/d8fWztmBk2/ZvjWeYh25KoSoJ9KusQNqPbOP6ACIx9VWDgtfpcBNPFQoVk/iVhwuLrk2bR4PFQP8wyhcoJA3GDK3vWJ1xO+ddAx+LCihVRswpgQobe33WVzjtiRHn8aaadDOi1AF5xl0gOWEM9qasZ6Y8J5JU2O0lVQIDAQAB"
}

resource "cloudflare_record" "mxa" {
  zone_id=var.zone
  type="MX"
  name="mail"
  priority="10"
  value="mxa.eu.mailgun.org"
}

resource "cloudflare_record" "mxb" {
  zone_id=var.zone
  type="MX"
  name="mail"
  priority="10"
  value="mxb.eu.mailgun.org"
}

resource "cloudflare_record" "fastmail_mxa" {
  zone_id=var.zone
  type="MX"
  name="@"
  priority="10"
  value="in1-smtp.messagingengine.com"
}

resource "cloudflare_record" "fastmail_mxb" {
  zone_id=var.zone
  type="MX"
  name="@"
  priority="20"
  value="in2-smtp.messagingengine.com"
}

resource "cloudflare_page_rule" "cache_images" {
  zone_id = var.zone
  target = "https://imgz.org/*.*"
  priority = 1

  actions {
    browser_cache_ttl = 16070400
    cache_level = "cache_everything"
    edge_cache_ttl = 2419200
  }
}


resource "cloudflare_record" "io_v6_root" {
  zone_id=var.zone2
  type="AAAA"
  name="@"
  proxied="true"
  value="${var.ipv6_ip}"
}

resource "cloudflare_record" "io_v6_www" {
  zone_id=var.zone2
  type="AAAA"
  name="www"
  proxied="true"
  value="${var.ipv6_ip}"
}

resource "cloudflare_record" "io_root" {
  zone_id=var.zone2
  type="A"
  name="@"
  proxied="true"
  value="${var.ipv4_ip}"
}

resource "cloudflare_record" "io_www" {
  zone_id=var.zone2
  type="A"
  name="www"
  proxied="true"
  value="${var.ipv4_ip}"
}

resource "cloudflare_record" "io_tracking" {
  zone_id=var.zone2
  type="CNAME"
  name="tracking"
  value="api.elasticemail.com"
}

resource "cloudflare_record" "io_mg" {
  zone_id=var.zone2
  type="CNAME"
  name="email.mail"
  value="eu.mailgun.org"
}

resource "cloudflare_record" "io_brave_verification" {
  zone_id=var.zone2
  type="TXT"
  name="@"
  value="brave-ledger-verification=95e73833c2e2d140ec37779d3c7ed5890199869a0f53341a859410c26e478f58"
}

resource "cloudflare_record" "io_spf" {
  zone_id=var.zone2
  type="TXT"
  name="@"
  value="v=spf1 include:_spf.elasticemail.com include:eu.mailgun.org ~all"
}

resource "cloudflare_record" "io_elasticemail_dmarc" {
  zone_id = var.zone2
  name="_dmarc"
  type="TXT"
  value="v=DMARC1;p=none;pct=20;aspf=r;adkim=r;"
}

resource "cloudflare_record" "io_mx_domainkey" {
  zone_id=var.zone2
  type="TXT"
  name="api._domainkey"
  value="k=rsa;t=s;p=MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQCbmGbQMzYeMvxwtNQoXN0waGYaciuKx8mtMh5czguT4EZlJXuCt6V+l56mmt3t68FEX5JJ0q4ijG71BGoFRkl87uJi7LrQt1ZZmZCvrEII0YO4mp8sDLXC8g1aUAoi8TJgxq2MJqCaMyj5kAm3Fdy2tzftPCV/lbdiJqmBnWKjtwIDAQAB"
}

resource "cloudflare_record" "io_mxa" {
  zone_id=var.zone2
  type="MX"
  name="mail"
  priority="10"
  value="mxa.eu.mailgun.org"
}

resource "cloudflare_record" "io_mxb" {
  zone_id=var.zone2
  type="MX"
  name="mail"
  priority="10"
  value="mxb.eu.mailgun.org"
}

resource "cloudflare_record" "io_fastmail_mxa" {
  zone_id=var.zone2
  type="MX"
  name="@"
  priority="10"
  value="in1-smtp.messagingengine.com"
}

resource "cloudflare_record" "io_fastmail_mxb" {
  zone_id=var.zone2
  type="MX"
  name="@"
  priority="20"
  value="in2-smtp.messagingengine.com"
}

resource "cloudflare_page_rule" "io_cache_images" {
  zone_id = var.zone2
  target = "https://imgz.io/*.*"
  priority = 1

  actions {
    browser_cache_ttl = 16070400
    cache_level = "cache_everything"
    edge_cache_ttl = 2419200
  }
}

