provider "aws" {
    region = "eu-west-2"
}


data "aws_vpc" "main" {
  filter {
    name   = "tag:Name"
    values = ["c26-VPC"]
  }
}

data "aws_subnets" "public" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.main.id]
  }
  filter {
    name   = "tag:Name"
    values = ["c26-public-subnet-1", "c26-public-subnet-2"]
  }
}

data "aws_ami" "amazon_linux_2023" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-2023.*-x86_64"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }

  filter {
    name   = "root-device-type"
    values = ["ebs"]
  }
}

resource "aws_db_subnet_group" "rds" {
  name       = "c26-chloe-lmnh-db-subnet-group"
  subnet_ids = data.aws_subnets.public.ids
}

  
resource "aws_security_group" "rds_sg" {
  name        = "C26-chloe-lmnh-rds-sg"
  description = "Allow Postgres access from EC2"
  vpc_id      = data.aws_vpc.main.id
}

resource "aws_security_group" "ec2_sg" {
  name        = "c26-chloe-lmnh-ec2-sg"
  description = "Security group for pipeline EC2 instance"
  vpc_id      = data.aws_vpc.main.id
}

# Separate ingress rule for RDS
resource "aws_security_group_rule" "rds_ingress" {
  type                     = "ingress"
  from_port                = 5432
  to_port                  = 5432
  protocol                 = "tcp"
  security_group_id        = aws_security_group.rds_sg.id
  source_security_group_id = aws_security_group.ec2_sg.id
  description              = "Postgres access from EC2"
}

resource "aws_security_group_rule" "rds_ingress_laptop" {
  type              = "ingress"
  from_port         = 5432
  to_port           = 5432
  protocol          = "tcp"
  cidr_blocks       = ["0.0.0.0/0"]  
  security_group_id = aws_security_group.rds_sg.id
  description       = "PostgreSQL from laptop"
}

# Separate egress rules for EC2
resource "aws_security_group_rule" "ec2_egress_postgres" {
  type                     = "egress"
  from_port                = 5432
  to_port                  = 5432
  protocol                 = "tcp"
  security_group_id        = aws_security_group.ec2_sg.id
  source_security_group_id = aws_security_group.rds_sg.id
  description              = "Allow Postgres access to RDS"
}

resource "aws_security_group_rule" "ec2_egress_internet" {
  type              = "egress"
  from_port         = 0
  to_port           = 0
  protocol          = "-1"
  cidr_blocks       = ["0.0.0.0/0"]
  security_group_id = aws_security_group.ec2_sg.id
  description       = "Allow internet access"
}

resource "aws_security_group_rule" "ec2_ingress_ssh" {
  type              = "ingress"
  from_port         = 22
  to_port           = 22
  protocol          = "tcp"
  cidr_blocks       = ["0.0.0.0/0"]
  security_group_id = aws_security_group.ec2_sg.id
  description       = "SSH access"
}


resource "aws_db_instance" "c26_chloe_lmnh_db" {
  identifier             = "c26-chloe-lmnh-db"
  engine                 = "postgres"
  engine_version         = "16"
  instance_class         = "db.t3.micro"
  allocated_storage      = 10
  db_name                = "lmnh_database"
  username               = var.db_username
  password               = var.db_password
  db_subnet_group_name   = aws_db_subnet_group.rds.name
  vpc_security_group_ids = [aws_security_group.rds_sg.id]
  publicly_accessible    = true # needed to connect from your laptop; the subnets must also be public
  skip_final_snapshot    = true
  performance_insights_enabled = false
}


resource "aws_instance" "c26-chloe-pipeline_ec2" {
  ami                    = data.aws_ami.amazon_linux_2023.id
  instance_type          = "t3.micro"
  key_name               = "c26-chloe-lmnh-key"
  associate_public_ip_address = true  # Add this line
  
  subnet_id              = data.aws_subnets.public.ids[0]
  vpc_security_group_ids = [aws_security_group.ec2_sg.id]
  
  tags = {
    Name = "c26-chloe-lmnh-pipeline-ec2"
  }
}

output "ec2_public_ip" {
  value       = aws_instance.c26-chloe-pipeline_ec2.public_ip
  description = "Public IP of the pipeline EC2 instance"
}

output "rds_endpoint" {
  value       = aws_db_instance.c26_chloe_lmnh_db.address
  description = "Endpoint of the RDS instance"
}


