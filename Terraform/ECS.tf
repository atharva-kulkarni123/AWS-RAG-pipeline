resource "aws_ecs_cluster" "rag" {
  name = "rag-cluster"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }
}

resource "aws_cloudwatch_log_group" "rag_api" {
  name              = "/ecs/rag-api"
  retention_in_days = 7
}

resource "aws_security_group" "ecs" {
  name        = "rag-ecs-sg"
  description = "Security group for the RAG ECS service"
  vpc_id      = aws_vpc.main.id

  ingress {
    description = "RAG API"
    from_port   = 8080
    to_port     = 8080
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
    Name = "rag-ecs-sg"
  }
}

resource "aws_vpc_security_group_ingress_rule" "rds_from_ecs" {
  security_group_id            = aws_security_group.rds.id
  referenced_security_group_id = aws_security_group.ecs.id
  from_port                    = 5432
  to_port                      = 5432
  ip_protocol                  = "tcp"
  description                  = "PostgreSQL from ECS RAG service"
}

resource "aws_secretsmanager_secret" "rag_db" {
  name                    = "rag-api/db"
  description             = "Database credentials for the RAG ECS task"
  recovery_window_in_days = 0
}

resource "aws_secretsmanager_secret_version" "rag_db" {
  secret_id = aws_secretsmanager_secret.rag_db.id

  secret_string = jsonencode({
    DB_PASSWORD = var.db_password
  })
}

data "aws_iam_policy_document" "ecs_task_assume_role" {
  statement {
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }

    actions = ["sts:AssumeRole"]
  }
}

resource "aws_iam_role" "ecs_execution" {
  name               = "rag-ecs-execution-role"
  assume_role_policy = data.aws_iam_policy_document.ecs_task_assume_role.json
}

resource "aws_iam_role_policy_attachment" "ecs_execution_managed" {
  role       = aws_iam_role.ecs_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_iam_role_policy" "ecs_execution_secrets" {
  name = "rag-ecs-execution-secrets"
  role = aws_iam_role.ecs_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "secretsmanager:GetSecretValue"
      ]
      Resource = aws_secretsmanager_secret.rag_db.arn
    }]
  })
}

resource "aws_iam_role" "ecs_task" {
  name               = "rag-ecs-task-role"
  assume_role_policy = data.aws_iam_policy_document.ecs_task_assume_role.json
}

resource "aws_iam_role_policy" "ecs_task_permissions" {
  name = "rag-ecs-task-permissions"
  role = aws_iam_role.ecs_task.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:ListBucket"
        ]
        Resource = aws_s3_bucket.rag_documents.arn
      },
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject"
        ]
        Resource = "${aws_s3_bucket.rag_documents.arn}/*"
      },
      {
        Effect = "Allow"
        Action = [
          "bedrock:InvokeModel",
          "bedrock:Converse"
        ]
        Resource = "*"
      }
    ]
  })
}

resource "aws_ecs_task_definition" "rag_api" {
  family                   = "rag-api"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = "512"
  memory                   = "1024"
  execution_role_arn       = aws_iam_role.ecs_execution.arn
  task_role_arn            = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([
    {
      name      = "rag-api"
      image     = "atharvak2427/rag-app:v1"
      essential = true

      portMappings = [
        {
          containerPort = 8080
          hostPort      = 8080
          protocol      = "tcp"
        }
      ]

      environment = [
        { name = "AWS_REGION", value = var.aws_region },
        { name = "AWS_DEFAULT_REGION", value = var.aws_region },
        { name = "S3_BUCKET", value = var.bucket_name },
        { name = "BEDROCK_LLM_MODEL", value = "global.amazon.nova-2-lite-v1:0" },
        { name = "BEDROCK_EMBEDDING_MODEL", value = "amazon.titan-embed-text-v2:0" },
        { name = "DB_HOST", value = aws_db_instance.rag.address },
        { name = "DB_PORT", value = "5432" },
        { name = "DB_NAME", value = aws_db_instance.rag.db_name },
        { name = "DB_USER", value = var.db_username }
      ]

      secrets = [
        {
          name      = "DB_PASSWORD"
          valueFrom = "${aws_secretsmanager_secret.rag_db.arn}:DB_PASSWORD::"
        }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.rag_api.name
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = "ecs"
        }
      }

      healthCheck = {
        command     = ["CMD-SHELL", "python -c \"import urllib.request; urllib.request.urlopen('http://localhost:8080/health')\" || exit 1"]
        interval    = 30
        timeout     = 5
        retries     = 3
        startPeriod = 30
      }
    }
  ])
}

resource "aws_ecs_service" "rag_api" {
  name            = "rag-api"
  cluster         = aws_ecs_cluster.rag.id
  task_definition = aws_ecs_task_definition.rag_api.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  deployment_minimum_healthy_percent = 0
  deployment_maximum_percent         = 100

  network_configuration {
    subnets          = aws_subnet.public[*].id
    security_groups  = [aws_security_group.ecs.id]
    assign_public_ip = true
  }

  depends_on = [
    aws_iam_role_policy_attachment.ecs_execution_managed,
    aws_iam_role_policy.ecs_execution_secrets
  ]
}
 