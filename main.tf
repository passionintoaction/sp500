# provider credential
provider "aws" {
  region     = "ca-central-1"
  profile = "terraform-user"
  shared_credentials_files = ["/Users/sravya.polisetty/.aws/credentials"]
}

# Variables
# experiment version
variable "experiment_version" {
  description = "experiment version"
  type        = string
  default     = "v5"
}

# aws region name
variable "region_name" {
  description = "AWS region name"
  type        = string
  default     = "ca-central-1"
}

# project name
variable "project_name" {
  description = "Project name"
  type        = string
  default     = "ML_Cal_Streamlit"
}

# deployment stage
variable "stage" {
  description = "Deployment stage name"
  type        = string
  default     = "dev"
}

# zip files
data "archive_file" "data_file" {
  type = "zip"
  source_dir  = "${path.module}/source_code"
  output_path = "${path.module}/source_code.zip"
}

# Upload zip data to s3
resource "aws_s3_object" "s3_file" {
  bucket = "streamlit-ml-calculator"
  key    = "source_code/source_code.zip"
  source = data.archive_file.data_file.output_path
  etag = filemd5(data.archive_file.data_file.output_path)
}

# IAM role for EC2
resource "aws_iam_role" "ec2_role" {
  name               = "${var.project_name}_ec2_iam_role"
  assume_role_policy = <<-EOF
  {
    "Version": "2012-10-17",
    "Statement": [
      {
        "Action": "sts:AssumeRole",
        "Principal": {
          "Service": "ec2.amazonaws.com"
        },
        "Effect": "Allow"
      }
    ]
  }
  EOF

managed_policy_arns = [
    "arn:aws:iam::aws:policy/AmazonEC2FullAccess",
    "arn:aws:iam::aws:policy/AmazonS3FullAccess",
    "arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess",
    "arn:aws:iam::aws:policy/AmazonSageMakerFullAccess",
    "arn:aws:iam::aws:policy/AWSStepFunctionsFullAccess",
    "arn:aws:iam::aws:policy/AWSLambdaExecute",
    "arn:aws:iam::aws:policy/AWSLambda_FullAccess"]
}

# IAM role for EC2
resource "aws_iam_instance_profile" "ec2_profile" {
  name = "${var.project_name}_ec2_profile"
  role = aws_iam_role.ec2_role.name
}

# Create EC2 instance
resource "aws_instance" "ml_cal_server" {
  ami           = "ami-017cc9a54455fbd8e" 
  instance_type               = "t2.micro"
  key_name                    = "rnd_nodes"
  vpc_security_group_ids      = ["sg-03e6b13eacff57ee8"]
  subnet_id                   = "subnet-068d67099e94fb8ab"
  iam_instance_profile = aws_iam_instance_profile.ec2_profile.name
  depends_on = [aws_s3_object.s3_file]

  user_data = <<-EOF
  #!/bin/bash
  mkdir /home/ubuntu/source_code
  cd /home/ubuntu/source_code
  aws s3 cp s3://streamlit-ml-calculator/source_code/source_code.zip /home/ubuntu/source_code/
  unzip source_code.zip
  sudo chmod +x start_server.sh
  ./start_server.sh
  EOF


  tags = {
    Name = "${var.project_name}_${var.stage}_${var.experiment_version}"
  }
}


# Output
output "instance-private-ip" {
  value = aws_instance.ml_cal_server.private_ip
}
