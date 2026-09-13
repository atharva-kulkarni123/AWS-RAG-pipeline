// VPC Configuration
resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = {
    Name = "production-vpc"
  }
}


// Public Subnet Configuration 
resource "aws_subnet" "public" {
  count = 2

  vpc_id                  = aws_vpc.main.id
  cidr_block              = var.public_subnet_cidrs[count.index]
  availability_zone       = var.availability_zones[count.index]
  map_public_ip_on_launch = true

  tags = {
    Name = "public-subnet-${var.availability_zones[count.index]}"
    Tier = "public"
  }
}

// Private Subnet Configuration
resource "aws_subnet" "private" {
  count = 2

  vpc_id            = aws_vpc.main.id
  cidr_block        = var.private_subnet_cidrs[count.index]
  availability_zone = var.availability_zones[count.index]

  tags = {
    Name = "private-subnet-${var.availability_zones[count.index]}"
    Tier = "private"
  }
} 

// Isolated subnet configuration for RDS
resource "aws_subnet" "isolated" {
  count = 2

  vpc_id            = aws_vpc.main.id
  cidr_block        = var.isolated_subnet_cidrs[count.index]
  availability_zone = var.availability_zones[count.index]

  tags = {
    Name = "isolated-subnet-${var.availability_zones[count.index]}"
    Tier = "isolated"
  }
}

/*
                         AWS VPC
                     10.0.0.0/16
                           │
              ┌────────────┴────────────┐
              │                         │
            AZ-a                      AZ-b
              │                         │
       ┌──────┴──────┐           ┌──────┴──────┐
       │             │           │             │
    PUBLIC        PRIVATE      PUBLIC        PRIVATE
  10.0.1.0/24   10.0.11.0/24 10.0.2.0/24  10.0.12.0/24
       │             │           │             │
      ALB          ECS/Lambda    ALB         ECS/Lambda
       │             │           │             │
       │           NAT GW        │           NAT GW
       │             │           │             │
       └─────────────┴───────────┴─────────────┘
                           │
                    Internet Gateway
                           │
                        Internet


              ┌─────────────────────────────┐
              │        ISOLATED TIER        │
              │                             │
              │ AZ-a           AZ-b         │
              │ 10.0.21.0/24   10.0.22.0/24│
              │     │              │        │
              │    RDS         OpenSearch    │
              │                             │
              │ NO IGW                         │
              │ NO NAT                         │
              │ NO Internet route              │
              └─────────────────────────────┘
*/