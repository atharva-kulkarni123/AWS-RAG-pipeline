variable "aws_region" {
  description = "AWS region"
  type        = string
}

variable "vpc_cidr" {
  description = "VPC CIDR"
  type        = string
}

variable "availability_zones" {
  description = "Availability zones"
  type        = list(string)
}

variable "public_subnet_cidrs" {
  type = list(string)
}

variable "private_subnet_cidrs" {
  type = list(string)
}

variable "isolated_subnet_cidrs" {
  type = list(string)
}

variable "bucket_name" {
  description = "S3 bucket for RAG documents"
  type        = string
}

variable "ami_id" {
  description = "AMI ID"
  type        = string
}

variable "key_pair_name" {
  description = "Existing AWS EC2 key pair name"
  type        = string
  default     = "Default-key-pair"
}

variable "ssh_cidr" {
  description = "CIDR block allowed to SSH to the EC2 instance"
  type        = string
  default     = "0.0.0.0/0"
}

variable "db_username" {
  description = "RDS DB username"
  type        = string
  sensitive   = true
}

variable "db_password" {
  description = "RDS DB password"
  type        = string
  sensitive   = true
}