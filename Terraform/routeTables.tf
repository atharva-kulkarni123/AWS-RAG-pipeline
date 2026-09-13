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

// -------------------------------
// 2 Private Route table
resource "aws_route_table" "private" {
  count = 2

  vpc_id = aws_vpc.main.id

  tags = {
    Name = "private-route-table-${var.availability_zones[count.index]}"
  }
}

// Private subnets route outbound traffic through their local NAT Gateway:
resource "aws_route" "private_nat" {
  count = 2

  route_table_id         = aws_route_table.private[count.index].id
  destination_cidr_block = "0.0.0.0/0"
  nat_gateway_id         = aws_nat_gateway.main[count.index].id
}

// Associating the routes with the table
resource "aws_route_table_association" "private" {
  count = 2

  subnet_id = aws_subnet.private[count.index].id

  route_table_id = aws_route_table.private[count.index].id
}

// 2 Isolated route table 
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
| Tier     | Subnets | Route tables | Why?                                     |
| -------- | ------: | -----------: | ---------------------------------------- |
| Public   |       2 |        **1** | Both use IGW                             |
| Private  |       2 |        **2** | Each uses its AZ's NAT GW                |
| Isolated |       2 |        **2** | AZ-specific isolation/future flexibility |
*/