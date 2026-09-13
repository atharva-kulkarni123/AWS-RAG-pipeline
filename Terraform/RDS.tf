# ---------------------------------------------------------
# RDS PostgreSQL Subnet Group
# ---------------------------------------------------------

resource "aws_db_subnet_group" "rag" {
  name       = "rag-rds-subnet-group"
  subnet_ids = aws_subnet.isolated[*].id

  tags = {
    Name        = "rag-rds-subnet-group"
    Environment = "dev"
    Project     = "rag"
  }
}


# ---------------------------------------------------------
# RDS Security Group
# ---------------------------------------------------------

resource "aws_security_group" "rds" {
  name        = "rag-rds-sg"
  description = "Security group for RAG PostgreSQL RDS"
  vpc_id      = aws_vpc.main.id

  # PostgreSQL
  ingress {
    description = "PostgreSQL from private application subnets"
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"

    cidr_blocks = var.private_subnet_cidrs
  }

  # Outbound traffic
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "rag-rds-sg"
  }
}


# ---------------------------------------------------------
# RDS PostgreSQL
# ---------------------------------------------------------

resource "aws_db_instance" "rag" {
  identifier = "rag-postgres"

  engine         = "postgres"
  engine_version = "17"

  instance_class = "db.t4g.micro"

  allocated_storage     = 20
  max_allocated_storage = 100
  storage_type          = "gp3"

  db_name  = "ragdb"
  username = var.db_username
  password = var.db_password
  port     = 5432

  db_subnet_group_name = aws_db_subnet_group.rag.name

  vpc_security_group_ids = [
    aws_security_group.rds.id
  ]

  # IMPORTANT:
  # RDS stays private inside the isolated subnets.
  publicly_accessible = false

  # Development settings
  multi_az = false

  # Encryption
  storage_encrypted = true

  # Backups
  backup_retention_period = 7

  # Maintenance
  deletion_protection = false

  # Don't create final snapshot when destroying dev environment
  skip_final_snapshot = true

  tags = {
    Name        = "rag-postgres"
    Environment = "dev"
    Project     = "rag"
  }
}