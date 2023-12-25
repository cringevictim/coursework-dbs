import subprocess

compose_file_path = './docker-compose.yml'


def recreate_containers():
    try:
        # Stop and remove containers defined in the docker-compose file
        # subprocess.run(['docker-compose', '-f', compose_file_path, 'down', '--remove-orphans', '--volumes', '-t', '0'], check=True)

        # Recreate and start the containers
        subprocess.run(['docker-compose', '-f', compose_file_path, 'up', '-d', '--build'], check=True)

        # print("Containers have been deleted and recreated successfully.")

        # Reading python-backend logs
        subprocess.run('docker compose logs -f python-backend')

    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        print("Containers were not recreated.")


if __name__ == '__main__':
    recreate_containers()
