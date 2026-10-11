// 1 Public Route table
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name = "public-route-table"
  }
}

// Adding internet route:
resource "aws_route" "public_internet" {
  route_table_id         = aws_route_table.public.id
  destination_cidr_block = "0.0.0.0/0"
  gateway_id             = aws_internet_gateway.main.id
}

// Associating routes with both public subnets:
resource "aws_route_table_association" "public" {
  count = 2

  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

// Private subnets use one NAT Gateway per AZ for outbound access.
resource "aws_route_table" "private" {
  count = 2

  vpc_id = aws_vpc.main.id

  tags = {
    Name = "private-route-table-${var.availability_zones[count.index]}"
  }
}

resource "aws_route" "private_nat" {
  count = 2

  route_table_id         = aws_route_table.private[count.index].id
  destination_cidr_block = "0.0.0.0/0"
  nat_gateway_id         = aws_nat_gateway.main[count.index].id
}

resource "aws_route_table_association" "private" {
  count = 2

  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = aws_route_table.private[count.index].id
}

// Isolated route tables keep the database subnets off the internet.
resource "aws_route_table" "isolated" {
  count = 2

  vpc_id = aws_vpc.main.id

  tags = {
    Name = "isolated-route-table-${var.availability_zones[count.index]}"
  }
}

// Associate them
resource "aws_route_table_association" "isolated" {
  count = 2

  subnet_id = aws_subnet.isolated[count.index].id

  route_table_id = aws_route_table.isolated[count.index].id
}

/*
| Tier     | Subnets | Explicit route tables | Why?                                      |
| -------- | ------: | --------------------: | ----------------------------------------- |
| Public   |       2 |                 **1** | ALB and NAT Gateways; IGW route           |
| Private  |       2 |                 **2** | ECS; each AZ routes outbound through NAT |
| Isolated |       2 |                 **2** | RDS; no internet route                   |
*/