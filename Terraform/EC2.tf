resource "aws_instance" "ansible_controller" {
  ami           = var.ami_id
  instance_type = "t3.micro"
  subnet_id     = aws_subnet.public[0].id
  key_name      = var.key_pair_name

  associate_public_ip_address = true

  vpc_security_group_ids = [
    aws_security_group.ansible_sg.id
  ]
  user_data = templatefile("${path.module}/user_data.sh", {
    rds_endpoint = aws_db_instance.rag.address
    rds_port     = aws_db_instance.rag.port
    rds_database = aws_db_instance.rag.db_name
    rds_username = var.db_username
    rds_password = var.db_password
  })
  user_data_replace_on_change = true
  depends_on = [
    aws_db_instance.rag
  ]
  tags = {
    Name = "rag-ansible-controller"
  }
}

resource "aws_security_group" "ansible_sg" {
  name        = "ansible-controller-server-sg"
  description = "Security group for RAG PostgreSQL RDS"
  vpc_id      = aws_vpc.main.id

  # SSH administration
  ingress {
    description = "SSH administration"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.ssh_cidr]
  }

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
    Name = "ansible-controller-server-sg"
  }
}


// 1. Need to allow the sg the EC2 in the RDS sg
// 2. Need to somehow pass password also in the script as the env were not getting set via the script
