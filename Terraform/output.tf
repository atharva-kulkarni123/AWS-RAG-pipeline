output "vpc_id" {
  description = "VPC ID"
  value       = aws_vpc.main.id
}

output "public_subnet_ids" {
  description = "Public subnet IDs"
  value       = aws_subnet.public[*].id
}

output "private_subnet_ids" {
  description = "Private subnet IDs"
  value       = aws_subnet.private[*].id
}

output "isolated_subnet_ids" {
  description = "Isolated subnet IDs"
  value       = aws_subnet.isolated[*].id
}

output "nat_gateway_ids" {
  description = "NAT Gateway IDs"
  value       = aws_nat_gateway.main[*].id
}

output "rds_endpoint" {
  description = "RDS PostgreSQL endpoint"
  value       = aws_db_instance.rag.address
}

output "rds_port" {
  description = "RDS PostgreSQL port"
  value       = aws_db_instance.rag.port
}

output "rds_database" {
  description = "RDS database name"
  value       = aws_db_instance.rag.db_name
}

output "rds_username" {
  description = "RDS database username"
  value       = aws_db_instance.rag.username
  sensitive   = true
}

output "ansible_controller_public_ip" {
  description = "Public IP address for SSH access to the Ansible controller"
  value       = aws_instance.ansible_controller.public_ip
}