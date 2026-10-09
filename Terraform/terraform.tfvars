aws_region = "ap-south-1"

vpc_cidr = "10.0.0.0/16"

availability_zones = [
  "ap-south-1a",
  "ap-south-1b"
]

public_subnet_cidrs = [
  "10.0.1.0/24",
  "10.0.2.0/24"
]

private_subnet_cidrs = [
  "10.0.11.0/24",
  "10.0.12.0/24"
]

isolated_subnet_cidrs = [
  "10.0.21.0/24",
  "10.0.22.0/24"
]

db_username = "postgres"
db_password = "postgres"

bucket_name = "rag-documents-prod-234123"

ami_id = "ami-090d68841c2a28756"