#!/bin/bash

set -e

exec > >(tee /var/log/user-data.log | logger -t user-data -s 2>/dev/console) 2>&1

echo "======================================"
echo "Starting EC2 bootstrap"
echo "======================================"

dnf update -y

echo "Installing Ansible and Git..."

dnf install -y \
  ansible-core \
  git

echo "Ansible installed:"
ansible --version

export RDS_ENDPOINT="${rds_endpoint}"
export RDS_PORT="${rds_port}"
export RDS_DATABASE="${rds_database}"
export RDS_USERNAME="${rds_username}"
export RDS_PASSWORD="${rds_password}"

echo "RDS endpoint: $${RDS_ENDPOINT}"
echo "RDS database: $${RDS_DATABASE}"

echo "======================================"
echo "Cloning RAG project"
echo "======================================"

mkdir -p /opt/rag-project

cd /opt

if [ ! -d "/opt/rag-project/.git" ]; then
    git clone https://github.com/atharva-kulkarni123/AWS-RAG-pipeline.git rag-project   # check path /opt/rag-project for the Repo
else
    echo "Repository already exists"
fi

cd /opt/rag-project/ansible

echo "======================================"
echo "Running Ansible bootstrap"
echo "======================================"

ansible-playbook \
  -i inventory.ini \
  bootstrap.yml

echo "======================================"
echo "Running PostgreSQL schema setup"
echo "======================================"

ansible-playbook \
  -i inventory.ini \
  postgres_setup.yml

echo "======================================"
echo "Bootstrap completed successfully"
echo "======================================"