resource "aws_security_group" "alb" {
  name        = "rag-alb-sg"
  description = "Allow HTTP traffic to the RAG API load balancer"
  vpc_id      = aws_vpc.main.id

  ingress {
    description = "HTTP access to the RAG API"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "rag-alb-sg"
  }
}

resource "aws_lb" "rag_api" {
  name               = "rag-api-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = aws_subnet.public[*].id

  tags = {
    Name = "rag-api-alb"
  }
}

resource "aws_lb_target_group" "rag_api" {
  name        = "rag-api-tg"
  port        = 8080
  protocol    = "HTTP"
  target_type = "ip"
  vpc_id      = aws_vpc.main.id

  health_check {
    enabled             = true
    path                = "/health"
    protocol            = "HTTP"
    matcher             = "200"
    interval            = 30
    timeout             = 5
    healthy_threshold   = 2
    unhealthy_threshold = 3
  }

  tags = {
    Name = "rag-api-tg"
  }
}

resource "aws_lb_listener" "rag_api_http" {
  load_balancer_arn = aws_lb.rag_api.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.rag_api.arn
  }
}
