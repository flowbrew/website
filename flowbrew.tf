provider "aws" {
  region = "eu-west-1"
}

terraform {
  backend "s3" {
    bucket         = "flowbrew-terraform"
    dynamodb_table = "terraform-state-lock-dynamo"
    region         = "eu-west-1"
    key            = "terraform.tfstate"
  }
}
