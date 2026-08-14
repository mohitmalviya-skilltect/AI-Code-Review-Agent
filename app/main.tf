terraform {
  required_providers {
    random = {
      source  = "hashicorp/random"
      version = "~> 3.0"
    }
  }
}

provider "random" {}

# Generates a random cute pet name
resource "random_pet" "server_name" {
  length = "two"
}

# Generates a random alphanumeric string for suffixes
resource "random_string" "suffix" {
  length  = 6
  special = false
  upper   = false
}

# Generates a secure random password
resource "random_password" "secret" {
  length           = 16
  special          = true
  override_special = "!#$*&"
}

# Output the generated values
output "pet_name" {
  value = random_pet.server_name.name
}

output "random_suffix" {
  value = random_string.suffix.result
  
output "generated_password" {
  value     = random_password.secret.result
  sensitive = tr
}
