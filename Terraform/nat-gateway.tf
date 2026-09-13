// EIP for NAT gateway
resource "aws_eip" "nat" {
  count = 2

  domain = "vpc"

  tags = {
    Name = "nat-eip-${count.index + 1}"
  }
}

// NAT gateway 
resource "aws_nat_gateway" "main" {
  count = 2

  allocation_id = aws_eip.nat[count.index].id
  subnet_id     = aws_subnet.public[count.index].id

  tags = {
    Name = "nat-gateway-${var.availability_zones[count.index]}"
  }

  depends_on = [
    aws_internet_gateway.main
  ]
}

