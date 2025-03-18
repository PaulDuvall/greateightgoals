#!/usr/bin/env bats
# test_run_sh.bats
# This test suite runs through all run.sh options to ensure they are working correctly.
# A 10-second timeout is applied to every command to prevent hangs.

setup() {
  # Create a temporary directory for testing.
  tmpdir=$(mktemp -d)
  cp "$BATS_TEST_DIRNAME/../run.sh" "$tmpdir/"

  # Set TEST_MODE so that run.sh skips interactive prompts.
  export TEST_MODE=1

  # Create fake bin directory for fake executables.
  mkdir -p "$tmpdir/fake_bin"

  # Create a fake AWS CLI to simulate authentication and SSM parameter retrieval.
  cat <<'EOF' > "$tmpdir/fake_bin/aws"
#!/bin/bash
# Fake AWS CLI for testing purposes.
if [[ "$1" == "sts" && "$2" == "get-caller-identity" ]]; then
  echo '{"Account": "123456789012"}'
  exit 0
fi
if [[ "$1" == "ssm" && "$2" == "get-parameter" ]]; then
  # Always return a dummy value to bypass interactive prompting.
  echo "dummy"
  exit 0
fi
if [[ "$1" == "ssm" && "$2" == "put-parameter" ]]; then
  echo "dummy"
  exit 0
fi
exit 0
EOF
  chmod +x "$tmpdir/fake_bin/aws"

  # Create a fake python3 to intercept "python3 -m venv .venv" and create a dummy virtual environment.
  cat <<'EOF' > "$tmpdir/fake_bin/python3"
#!/bin/bash
if [[ "$1" == "-m" && "$2" == "venv" && "$3" == ".venv" ]]; then
  mkdir -p .venv/bin
  echo "#!/bin/bash" > .venv/bin/activate
  echo "echo 'Activating virtualenv'" >> .venv/bin/activate
  chmod +x .venv/bin/activate
  exit 0
fi
# Handle any python3 command and just echo what would be executed
echo "$@"
exit 0
EOF
  chmod +x "$tmpdir/fake_bin/python3"

  # Create a fake python to handle "python -m pytest"
  cat <<'EOF' > "$tmpdir/fake_bin/python"
#!/bin/bash
if [[ "$1" == "-m" && "$2" == "pytest" ]]; then
  echo "All tests passed!"
  exit 0
fi
# Handle any python command and just echo what would be executed
echo "$@"
exit 0
EOF
  chmod +x "$tmpdir/fake_bin/python"

  # Create a fake pip to simulate package installations.
  cat <<'EOF' > "$tmpdir/fake_bin/pip"
#!/bin/bash
echo "Fake pip: $@"
exit 0
EOF
  chmod +x "$tmpdir/fake_bin/pip"

  # Prepend fake_bin to PATH.
  export PATH="$tmpdir/fake_bin:$PATH"

  # Create an empty requirements.txt file.
  echo "" > "$tmpdir/requirements.txt"

  # Create a dummy main.py that simulates behavior for stats and email commands.
  cat <<'EOF' > "$tmpdir/main.py"
#!/usr/bin/env python3
import sys
if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "stats":
        print("Ovechkin stats")
    elif len(sys.argv) > 1 and sys.argv[1] == "email":
        print("Email sent to default recipient")
    elif len(sys.argv) > 1 and sys.argv[1] == "email-to":
        print("Email sent to " + sys.argv[2])
EOF
  chmod +x "$tmpdir/main.py"

  # Create a dummy Lambda folder and file.
  mkdir -p "$tmpdir/lambda"
  cat <<'EOF' > "$tmpdir/lambda/lambda_function.py"
#!/usr/bin/env python3
print("Lambda function executed")
EOF
  chmod +x "$tmpdir/lambda/lambda_function.py"

  # Create a dummy lambda requirements file
  echo "" > "$tmpdir/lambda/requirements-lambda.txt"

  # Create a dummy aws-static-website folder and update_website.py.
  mkdir -p "$tmpdir/aws-static-website"
  cat <<'EOF' > "$tmpdir/aws-static-website/update_website.py"
#!/usr/bin/env python3
print("Website updated successfully")
EOF
  chmod +x "$tmpdir/aws-static-website/update_website.py"

  # Create a dummy tests directory with a Lambda local test script.
  mkdir -p "$tmpdir/tests"
  cat <<'EOF' > "$tmpdir/tests/test_lambda_local.py"
#!/usr/bin/env python3
print("Lambda local test executed")
EOF
  chmod +x "$tmpdir/tests/test_lambda_local.py"

  # Create a dummy pytest test file so that the "test" command has something to run.
  mkdir -p "$tmpdir/tests"
  cat <<'EOF' > "$tmpdir/tests/test_sample.py"
def test_dummy():
    assert True
EOF

  # Create a dummy .env file for the email test
  cat <<'EOF' > "$tmpdir/.env"
# Ovechkin Tracker Email Configuration
AWS_REGION=us-east-1
SENDER_EMAIL=test@example.com
RECIPIENT_EMAIL=recipient@example.com
EOF

  # Change directory to tmpdir so that run.sh uses it as its working directory.
  pushd "$tmpdir" > /dev/null
}

teardown() {
  popd > /dev/null
  rm -rf "$tmpdir"
}

# Helper function to run commands with a 10-second timeout.
run_with_timeout() {
  run timeout 10 "$@"
}

@test "run.sh help displays usage" {
  run_with_timeout bash run.sh help
  [ "$status" -eq 0 ]
  echo "$output" | grep -q "Usage: ./run.sh"
}

@test "run.sh setup creates virtual environment" {
  run_with_timeout bash run.sh setup
  [ "$status" -eq 0 ]
  [ -d ".venv" ]
}

@test "run.sh setup-lambda creates virtual environment and installs Lambda deps" {
  run_with_timeout bash run.sh setup-lambda
  [ "$status" -eq 0 ]
  [ -d ".venv" ]
}

@test "run.sh stats displays Ovechkin stats" {
  # Create .venv directory to skip setup
  mkdir -p "$tmpdir/.venv/bin"
  echo "#!/bin/bash" > "$tmpdir/.venv/bin/activate"
  echo "echo 'Activating virtualenv'" >> "$tmpdir/.venv/bin/activate"
  chmod +x "$tmpdir/.venv/bin/activate"
  
  run_with_timeout bash run.sh stats
  [ "$status" -eq 0 ]
  echo "$output" | grep -q "Ovechkin stats"
}

@test "run.sh email sends email using default recipient" {
  # Create .venv directory to skip setup
  mkdir -p "$tmpdir/.venv/bin"
  echo "#!/bin/bash" > "$tmpdir/.venv/bin/activate"
  echo "echo 'Activating virtualenv'" >> "$tmpdir/.venv/bin/activate"
  chmod +x "$tmpdir/.venv/bin/activate"
  
  run_with_timeout bash run.sh email
  [ "$status" -eq 0 ]
  echo "$output" | grep -q "Attempting to send email"
}

@test "run.sh email-to sends email to specified address" {
  # Create .venv directory to skip setup
  mkdir -p "$tmpdir/.venv/bin"
  echo "#!/bin/bash" > "$tmpdir/.venv/bin/activate"
  echo "echo 'Activating virtualenv'" >> "$tmpdir/.venv/bin/activate"
  chmod +x "$tmpdir/.venv/bin/activate"
  
  run_with_timeout bash run.sh email-to test@example.com
  [ "$status" -eq 0 ]
  echo "$output" | grep -q "Attempting to send email to test@example.com"
}

@test "run.sh configure creates .env file with provided values" {
  # Create .venv directory to skip setup
  mkdir -p "$tmpdir/.venv/bin"
  echo "#!/bin/bash" > "$tmpdir/.venv/bin/activate"
  echo "echo 'Activating virtualenv'" >> "$tmpdir/.venv/bin/activate"
  chmod +x "$tmpdir/.venv/bin/activate"
  
  # Remove existing .env file
  rm -f "$tmpdir/.env"
  
  run_with_timeout bash -c "printf 'us-west-2\nsender@example.com\nrecipient@example.com\n' | bash run.sh configure"
  [ "$status" -eq 0 ]
  [ -f ".env" ]
  run grep -q "AWS_REGION=us-west-2" ".env"
  [ "$status" -eq 0 ]
  run grep -q "SENDER_EMAIL=sender@example.com" ".env"
  [ "$status" -eq 0 ]
  run grep -q "RECIPIENT_EMAIL=recipient@example.com" ".env"
  [ "$status" -eq 0 ]
}

@test "run.sh test-lambda runs test Lambda local script" {
  # Create .venv directory to skip setup
  mkdir -p "$tmpdir/.venv/bin"
  echo "#!/bin/bash" > "$tmpdir/.venv/bin/activate"
  echo "echo 'Activating virtualenv'" >> "$tmpdir/.venv/bin/activate"
  chmod +x "$tmpdir/.venv/bin/activate"
  
  run_with_timeout bash run.sh test-lambda
  [ "$status" -eq 0 ]
  echo "$output" | grep -q "Testing Lambda function locally"
}

@test "run.sh test runs all tests" {
  # Create .venv directory to skip setup
  mkdir -p "$tmpdir/.venv/bin"
  echo "#!/bin/bash" > "$tmpdir/.venv/bin/activate"
  echo "echo 'Activating virtualenv'" >> "$tmpdir/.venv/bin/activate"
  chmod +x "$tmpdir/.venv/bin/activate"
  
  run_with_timeout bash run.sh test
  [ "$status" -eq 0 ]
  echo "$output" | grep -q "All tests passed"
}

@test "run.sh install-test-deps installs pytest-cov" {
  # Create .venv directory to skip setup
  mkdir -p "$tmpdir/.venv/bin"
  echo "#!/bin/bash" > "$tmpdir/.venv/bin/activate"
  echo "echo 'Activating virtualenv'" >> "$tmpdir/.venv/bin/activate"
  chmod +x "$tmpdir/.venv/bin/activate"
  
  run_with_timeout bash run.sh install-test-deps
  [ "$status" -eq 0 ]
  echo "$output" | grep -q "Test dependencies installed successfully"
}

@test "run.sh update-website updates the website" {
  # Create .venv directory to skip setup
  mkdir -p "$tmpdir/.venv/bin"
  echo "#!/bin/bash" > "$tmpdir/.venv/bin/activate"
  echo "echo 'Activating virtualenv'" >> "$tmpdir/.venv/bin/activate"
  chmod +x "$tmpdir/.venv/bin/activate"
  
  run_with_timeout bash run.sh update-website
  [ "$status" -eq 0 ]
  echo "$output" | grep -q "Website updated successfully"
}

@test "run.sh unknown command returns error" {
  run_with_timeout bash run.sh nonexistent_command
  [ "$status" -eq 1 ]
  echo "$output" | grep -q "Unknown command"
}
