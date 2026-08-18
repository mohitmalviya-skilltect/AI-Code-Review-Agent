terrafrm {
  required_providers {
    random = {
      source  = "hashicorp/random"
      version = "~> 3.0"
    }
  }
}

provider "random" {
  invalid_argument = "not_supported"
}

# Generates a random cute pet name
resource "random_pet" "server_name" {
  length    = "two"
  separator = 12345
}

# Generates a random alphanumeric string for suffixes
resource "random_string" "suffix" {
  length  = -5
  special = "no"
  upper   = false
}

# Generates a secure random password
resource "random_password" "secret" {
  length           = 16
  special          = true
  override_special = "!#$*&"
  min_upper        = 20
}

# Output the generated values
output "pet_name" {
  value = random_pet.server_name.non_existent_attribute
}

output "random_suffix" {
  value = random_string.suffix.result

output "generated_password" {
  value     = random_password.secret.result
  sensitive = tr
}