![DevOps Concept](https://images.unsplash.com/photo-1618401471353-b98afee0b2eb?auto=format&fit=crop&w=1200&q=80)

# Session 30 — DevOps Fundamentals: Complete Detailed Notes

> Covers: Physical Servers → Virtual Machines → Containers (Docker) → Container Registry → Deployment (EC2) → Container Orchestration → Monolithic vs Microservices architecture.
> These notes expand on the original session notes with deeper explanations, diagrams-in-text, real-world examples, and an interview Q&A section with follow-ups.

---

## Table of Contents
1. [The Core Problem: Running Apps on Physical Servers](#1-the-core-problem)
2. [Virtual Machines (VMs)](#2-virtual-machines)
3. [Containerization & Docker](#3-containerization--docker)
4. [Container Registry](#4-container-registry)
5. [Deploying a Container (End-to-End on AWS EC2)](#5-deploying-a-container)
6. [Container Orchestration](#6-container-orchestration)
7. [Monolithic Architecture](#7-monolithic-architecture)
8. [Microservices Architecture](#8-microservices-architecture)
9. [The Big Picture / Evolution Timeline](#9-the-big-picture)
10. [Interview Questions, Answers & Follow-ups](#10-interview-questions)
11. [Quick Revision Cheat Sheet](#11-cheat-sheet)

---

## 1. The Core Problem

![Physical Servers in Data Center](https://images.unsplash.com/photo-1558494949-ef010cbdcc31?auto=format&fit=crop&w=800&q=80)

### Why not just run everything on one physical server?

**The constraint:** Historically, teams ran *one* web application per physical server. Why?

| # | Issue | Explanation |
|---|-------|-------------|
| 1 | **Resource contention** | All apps share the same OS & hardware. If one app spikes CPU/RAM, the others slow down or crash ("noisy neighbour" problem). |
| 2 | **Compatibility conflicts** | App A needs Python 3.8 + libssl 1.0; App B needs Python 3.11 + libssl 3.0. They cannot coexist cleanly on one OS. (This is the classic *"dependency hell"*.) |
| 3 | **Security blast radius** | If one app is compromised, the attacker can pivot to every other app on the same machine. |

**The resulting business problems:**
- **Resource wastage** — A server sized for peak load sits ~10–15% utilized most of the time.
- **High cost** — More physical servers = more hardware, power, cooling, rack space, and admin effort.

> **Two qualities we ultimately want from any solution (from the handwritten margin notes):**
> - **Highly Available** — the app stays up even if something fails.
> - **Scalable** — we can add capacity quickly when traffic grows.

➡️ This pain led to **Virtualization → Virtual Machines.**

---

## 2. Virtual Machines

### Definition
A **Virtual Machine (VM)** is a software-based emulation of a physical computer. VMs are created by a **hypervisor** (virtualization software) that lets multiple VMs share one physical machine. Each VM is an **independent, isolated environment** with its **own Guest OS**, applications, and allocated resources.

### Architecture (stack)
```
┌──────────┬──────────┬──────────┐
│   App    │   App    │   App    │   ← one app per VM
├──────────┼──────────┼──────────┤
│ Guest OS │ Guest OS │ Guest OS │   ← FULL OS per VM (heavy!)
├──────────┴──────────┴──────────┤
│          Hypervisor             │   ← creates/manages VMs
├─────────────────────────────────┤
│        Host Operating System    │   (Type-2) 
├─────────────────────────────────┤
│           Host Hardware         │
└─────────────────────────────────┘
```

### Hypervisor — two types (added context)
| Type | Name | Runs on | Examples | Use case |
|------|------|---------|----------|----------|
| **Type 1** | Bare-metal | Directly on hardware | VMware ESXi, Microsoft Hyper-V, Xen, KVM | Data centers, cloud |
| **Type 2** | Hosted | On top of a host OS | VirtualBox, VMware Workstation | Laptops/dev machines |

> ☁️ **Cloud connection:** AWS **EC2**, GCP **Compute Engine**, and Azure **Virtual Machines** are essentially VMs you rent. The session diagram maps `AWS / GCP / Azure → EC2 → server (application)`.

### Key Properties of VMs
1. **Isolation** — A crash or breach in one VM does **not** affect other VMs or the host.
2. **Independence** — Run different OSes side by side (e.g., Windows VM + Linux VM on the same box).
3. **Resource Allocation** — VMs share physical CPU/memory/storage; the hypervisor divides them up.
4. **Encapsulation** — A VM is just a set of files → easy to **move, copy, snapshot, and back up**.

### Disadvantages of VMs
- **Limited Portability** — Moving VMs across hypervisors/clouds is hard; images are **large (GBs)**. Painful to pass between dev → test → prod teams.
- **Inefficient Scaling** — Each VM boots a **full OS**, so startup is **slow (minutes)**. Slow restarts hurt availability.
- **OS Licensing cost** — Each VM may need its **own OS license** → costs explode at scale (the note literally shows *"50 OS / 50 VM"* = 50 separate OS installs).

> 🔑 **The lingering problem:** VMs solved isolation, but each one still drags an **entire Guest OS** along. If I have 50 apps, I'm running 50 OSes. **Wasteful.**
> ➡️ Solution: share the OS kernel but keep apps isolated → **Containers.**

---

## 3. Containerization & Docker

### Definition
**Containerization** is a **lightweight form of virtualization** that runs multiple **isolated** applications on a **single host OS**. You package an application **plus its dependencies** into a **container**.

A **container** is a standardized unit of software that bundles **code + runtime + system tools + libraries + settings** needed to run the app — so it runs the same everywhere ("**works on my machine**" → "**works everywhere**").

### VM vs Container — the key diagram
![Containers vs Virtual Machines Diagram](https://upload.wikimedia.org/wikipedia/commons/thumb/a/a5/Container-vm-whatcontainer_2.png/800px-Container-vm-whatcontainer_2.png)

```
        CONTAINERS                              VIRTUAL MACHINES
┌──────┬──────┬──────┐                  ┌────────┬────────┬────────┐
│ App A│ App B│ App C│                  │ App A  │ App B  │ App C  │
│Bins/ │Bins/ │Bins/ │                  │Bins/Lib│Bins/Lib│Bins/Lib│
│ Libs │ Libs │ Libs │                  ├────────┼────────┼────────┤
├──────┴──────┴──────┤                  │GuestOS │GuestOS │GuestOS │ ← heavy
│   Docker Engine    │ ← shares kernel  ├────────┴────────┴────────┤
├────────────────────┤                  │       Hypervisor         │
│      Host OS        │                  ├──────────────────────────┤
│   (kernel shared)   │                  │        Host OS           │
├────────────────────┤                  ├──────────────────────────┤
│   Infrastructure    │                  │     Infrastructure       │
└────────────────────┘                  └──────────────────────────┘
   LIGHT, fast (sec)                          HEAVY, slow (min)
```
**The crucial difference:** Containers **share the host OS kernel** — there is **no Guest OS per container**. VMs virtualize *hardware*; containers virtualize the *OS*.

| Aspect | Virtual Machine | Container |
|--------|-----------------|-----------|
| Isolation unit | Full OS | Process (shares kernel) |
| Size | GBs | MBs |
| Startup | Minutes | Seconds / milliseconds |
| Overhead | High (full OS each) | Low |
| Portability | Limited | Excellent |
| Isolation strength | Stronger (hardware-level) | Weaker (OS-level) |
| OS licensing | Per VM | Shared |

### How containers achieve isolation (Linux internals — added depth)
Docker doesn't use a hypervisor. It uses two Linux kernel features:

1. **Namespaces → Isolation.** Create separate "compartments" so each container sees its own files, network, process IDs, hostname, users — as if it were its own mini-computer. (Types: `pid`, `net`, `mnt`, `uts`, `ipc`, `user`.)
2. **cgroups (control groups) → Resource limiting.** Track and **cap** how much CPU, memory, disk I/O, and network each group of processes can use → fair sharing, prevents one container hogging the machine.

> 🧠 **Memory hook:** *Namespaces = what a container can **see**. cgroups = how much it can **use**.*

<img src="https://upload.wikimedia.org/wikipedia/commons/thumb/4/4e/Docker_%28container_engine%29_logo.svg/512px-Docker_%28container_engine%29_logo.svg.png" alt="Docker Engine" width="300"/>

### Docker — core components
- **Docker Engine** — the core runtime that **builds and runs** containers (client-server: `dockerd` daemon + CLI + REST API).
- **Container runtime** — the low-level piece that actually starts containers (e.g., `containerd`, `runc`).

### How to create Docker containers — the three pillars
| Term | What it is | Analogy |
|------|-----------|---------|
| **Dockerfile** | A text file of **instructions** to build an image | The **recipe** |
| **Docker Image** | A **read-only template** built from the Dockerfile | The **cake mould / blueprint** |
| **Docker Container** | A **running instance** of an image | The **actual running cake** |

> Relationship: **Dockerfile → (build) → Image → (run) → Container.** One image can spawn many identical containers (this is how you scale).

### Benefits of containers
1. **Portability** — same image runs on laptop, server, any cloud.
2. **Scalability** — spin up many container copies in seconds.
3. *(added)* **Consistency** across dev/test/prod, **efficiency** (high density per host), **fast CI/CD**.

### Docker in Machine Learning (added — the note asks this)
- Package an **ML model + exact library versions** (TensorFlow/PyTorch/sklearn, CUDA) into one image → **reproducibility**, no "version drift."
- Serve a model behind an API (Flask/FastAPI) in a container → easy deploy & scale.
- Each ML microservice (preprocessing, model A, model B) ships as its own container.

---

## 4. Container Registry

### Definition

![Docker Architecture](https://docs.docker.com/engine/images/architecture.webp)
*Official Docker Architecture Diagram illustrating how the Docker Client pushes/pulls images to and from the Docker Registry.*

A **container registry** is a **centralized repository** that **stores, manages, and distributes** container images. Like a source-code repo (GitHub), but **for images**.

> Flow: `docker build` → image on your machine → `docker push` → **registry** → `docker pull` from anywhere → `docker run`.

### Key features
1. **Image Storage** — store images (public or private).
2. **Versioning** — tag images (`v1.0`, `v2.3`, `latest`) → track and roll back.
3. **Distribution** — push once, pull anywhere → deploy across environments.
4. **Access Control** — who can push/pull (critical for security in enterprises).
5. **CI/CD Integration** — pipelines auto-build, store, and deploy images.

### Examples
- **Docker Hub** (public default)
- **Amazon ECR** (Elastic Container Registry — AWS)
- **Google GCR / Artifact Registry** (GCP)
- *(added)* **Azure ACR**, **GitHub Container Registry (GHCR)**

> 🏷️ **Tag anatomy:** `myregistry.com/myapp:v1.2` = `<registry>/<repository>:<tag>`. Avoid relying on `latest` in production — it's ambiguous and breaks reproducible deploys.

---

## 5. Deploying a Container
### End-to-end: from code to running on the internet (AWS EC2)

<img src="https://upload.wikimedia.org/wikipedia/commons/thumb/9/93/Amazon_Web_Services_Logo.svg/512px-Amazon_Web_Services_Logo.svg.png" alt="AWS Logo" width="150"/>

#### Build & ship steps
**Step 1 — Prepare your application.** Have the code + dependencies ready; plan a project structure and a Dockerfile.

**Step 2 — Write a Dockerfile.** Example for a Node.js app:
```dockerfile
# Use an official Node.js runtime as a parent image
FROM node:14

# Set the working directory inside the container
WORKDIR /usr/src/app

# Copy package files first (better layer caching)
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy the rest of the application code
COPY . .

# Expose the port the app runs on
EXPOSE 8080

# Command to run the application
CMD ["node", "app.js"]
```
*(Added) Common Dockerfile instructions:*
| Instruction | Purpose |
|-------------|---------|
| `FROM` | Base image to start from |
| `WORKDIR` | Set working directory |
| `COPY` / `ADD` | Copy files into the image |
| `RUN` | Execute a command **at build time** (e.g., install deps) |
| `EXPOSE` | Document the port the app listens on |
| `CMD` | Default command **at run time** (one per Dockerfile) |
| `ENTRYPOINT` | Fixed executable; args appended |
| `ENV` | Set environment variables |

> 💡 **Why `COPY package*.json` before `COPY . .`?** Docker caches layers. Dependencies change rarely, so this avoids re-running `npm install` on every code change → faster builds.

**Step 3 — Build the image:**
```bash
docker build -t myapp:latest .
```
(`-t` = tag/name, `.` = build context / where the Dockerfile is.)

**Step 4 — Test locally:**
```bash
docker run -d -p 8080:8080 myapp:latest
```
(`-d` = detached/background, `-p host:container` = port mapping.)

**Step 5 — Push to a container registry:**
```bash
docker login
docker tag myapp:latest myregistry.com/myapp:latest
docker push myregistry.com/myapp:latest
```

#### Deploy on AWS EC2 (make it public)
1. **Launch an EC2 instance**
   - Log in to **AWS Management Console** → **EC2 Dashboard** → **Launch Instance**.
   - Choose an **AMI** (e.g., *Amazon Linux 2*).
   - Choose **instance type** (e.g., `t2.micro` — free-tier eligible).
   - Configure details, **add storage** (8 GB usually fine), add tags.
   - **Security Group:** allow **SSH (port 22)** and your app's port (**HTTP 80 / 8080**).
   - **Download the Key Pair** (`.pem` file) — store it securely; you can't re-download it.
2. **Connect to the instance** (SSH):
   ```bash
   ssh -i mykey.pem ec2-user@<public-ip>
   ```
3. **Install Docker** on the instance:
   ```bash
   sudo yum update -y
   sudo yum install docker -y
   sudo service docker start
   ```
4. **Pull & run the image** from the registry:
   ```bash
   docker login
   docker pull <your-dockerhub-username>/myapp:latest
   docker run -d -p 80:8080 <your-dockerhub-username>/myapp:latest
   ```
   Now mapping host **port 80** → container **port 8080** makes it reachable over **HTTP** on the EC2 public IP.
5. **Make it available to the internet** — the Security Group inbound rule for port 80 + the public IP/DNS = anyone can reach your app.

> 🔐 **Security note (added):** Open only the ports you need. Port 22 should ideally be limited to your IP. Put a load balancer / reverse proxy (Nginx) in front for TLS (HTTPS).

---

## 6. Container Orchestration

### Definition

<img src="https://upload.wikimedia.org/wikipedia/commons/thumb/3/39/Kubernetes_logo_without_workmark.svg/512px-Kubernetes_logo_without_workmark.svg.png" alt="Kubernetes Logo" width="150"/>

**Container orchestration** = automatically **managing, coordinating, and scaling** containerized apps. Think of it as a **smart manager** for your containers.

### What it handles
- **Start/stop containers** — keep apps running.
- **Scaling** — add/remove containers based on load.
- **Networking** — let containers talk to each other and the outside world.
- **Health monitoring** — check health; **restart** failed containers (self-healing).
- **Rolling updates** — push new versions with **zero downtime**.

### When do you actually need it?

**Scenario 1 — High Availability & High Scalability for a single service**
1. **High Availability** — platform monitors the container; auto-restarts on crash.
2. **Auto-scaling** — during a sale/marketing spike, automatically add container instances; remove them after.
3. **Rolling Updates** — gradually replace old containers with new ones → **zero downtime**.
4. **Resource Optimization** — allocate resources dynamically based on current load.

**Scenario 2 — Microservices**
When you have **many containers** (multiple services, e.g., the note's `score` service + `win-probability` service, or **multiple ML models**), you need orchestration to:
- deploy each service's container,
- scale each **independently** (the note: *container → copies → scale*),
- wire up networking and handle failures across the fleet.

> The recurring theme in the diagrams: **"more than one container"** → manual management breaks down → you need an orchestrator.

### Tools (added)
- **Kubernetes (K8s)** — the industry standard. Concepts: **Pod** (smallest unit, 1+ containers), **Node**, **Deployment**, **Service**, **ReplicaSet**, **Ingress**, **kubelet**, **control plane**.
- **Docker Swarm** — simpler, built into Docker.
- **Amazon ECS / EKS**, **Google GKE**, **Azure AKS** — managed cloud offerings.
- **Apache Mesos**, **Nomad** — alternatives.

---

## 7. Monolithic Architecture

### Definition
A **monolith** is a traditional design where the whole app is built and deployed as a **single, unified unit**. Simple at first, hard to scale/manage as it grows.

### Key Characteristics
1. **Single Codebase** — UI + business logic + data access all together.
2. **Tight Coupling** — a change in one part can affect others.
3. **Single Deployment Unit** — any change → **redeploy the whole app**.
4. **Same Tech Stack** — all components share the same dependencies → conflicts.

### Advantages
1. **Simplicity** — straightforward to develop, test, deploy (one thing).
2. **Performance** — in-process calls are fast (no network hops).
3. **Ease of Development** — great for **small** applications & small teams.

### Disadvantages
1. **Redeployment** — small change → redeploy everything.
2. **Scaling is all-or-nothing** — can't scale just the busy part.
3. **Dependency conflicts** — one shared stack for everything.
4. **Complexity & collaboration issues** as it grows (many devs in one codebase).
5. **Locked to one tech stack.**
6. **A bug in one part can crash the entire application.**

---

## 8. Microservices Architecture

### Definition

![Monolithic vs Microservices Architecture](https://martinfowler.com/articles/microservices/images/sketch.png)
*Standard industry diagram (by Martin Fowler) illustrating a Monolithic application versus a Microservices architecture.*

**Microservices** split the app into **small, independent services**, each owning a **specific business capability**, each **developed, deployed, and scaled independently**.

### Key Characteristics
1. **Independence** — each service runs on its own; talks via well-defined **APIs** (HTTP/HTTPS or message queues).
2. **Single Responsibility** — one service = one business function (SRP).
3. **Decentralized Data** — each service can own its **own database** (best fit for its needs).
4. **Independent Scalability** — scale only the services under load.
5. **Technology Diversity** — different languages/frameworks/DBs per service.
6. **Autonomous Teams** — teams own services end-to-end → faster cycles.

### How do microservices communicate?
1. **APIs** — synchronous request/response, usually **REST** or **gRPC**.
2. **Message Brokers** — asynchronous (e.g., **Kafka, RabbitMQ, SQS**) → decoupling, buffering.
3. **Service Mesh** — infra layer (e.g., **Istio, Linkerd**) handling service-to-service traffic, retries, security, observability.

### Advantages
1. **Scalability** — scale individual services on demand.
2. **Flexibility** — best tool per job (polyglot).
3. **Resilience** — one service failing doesn't necessarily down the whole app.
4. **Faster Time to Market** — independent deploys → faster releases.
5. **Easier Maintenance** — smaller codebases are easier to understand.

### Disadvantages
1. **Complexity** — many moving parts; needs strong DevOps.
2. **Distributed-systems challenges** — network latency, security, **data consistency**.
3. **Increased resource usage** — more services = more overhead than a monolith.
4. **Monitoring & Debugging** — tracing a request across services is hard → need **distributed tracing** (Jaeger/Zipkin), centralized logging.

### How containers fit into microservices
Each microservice is packaged into **its own container**, giving:
1. **Isolation** 2. **Portability** 3. **Scalability** 4. **Ease of deployment** 5. **Fault tolerance**
> 🔗 This is exactly **why containers + orchestration (Kubernetes) became the backbone of microservices.**

### Microservices in the ML universe (added — note asks this)
- Separate services for **data preprocessing**, **feature store**, **model inference**, **post-processing**.
- Multiple **models served as independent endpoints** (e.g., a "score" model and a "win-probability" model — from the diagrams) — each scaled by its own traffic.
- Enables **A/B testing**, **canary model rollouts**, and **independent retraining/deploys**.

---

## 9. The Big Picture
### Evolution timeline (added — ties everything together)
```
Physical Servers            → 1 app per box, wasteful, costly
   │  (isolation + better utilization)
   ▼
Virtual Machines            → many OSes per box, but heavy & slow
   │  (drop the per-app Guest OS; share the kernel)
   ▼
Containers (Docker)         → lightweight, portable, fast
   │  (managing many containers by hand is hard)
   ▼
Container Orchestration     → Kubernetes auto-scales/heals the fleet
   │  (pairs naturally with…)
   ▼
Microservices architecture  → small independent services in containers
```
**One-line story for interviews:** *"We moved from physical servers (wasteful) → VMs (isolation but heavy OS overhead) → containers (lightweight, share the kernel) → orchestration (manage containers at scale) → which made microservices practical."*

---

## 10. Interview Questions
### With answers + follow-ups

### A. Virtualization & VMs

**Q1. What is a Virtual Machine and what is a hypervisor?**
**A.** A VM is a software emulation of a physical computer with its own Guest OS, apps, and virtualized resources. A **hypervisor** is the software layer that creates and manages VMs and divides the physical hardware among them.
- *Follow-up: Difference between Type 1 and Type 2 hypervisors?* → Type 1 (bare-metal) runs directly on hardware (ESXi, Hyper-V, KVM) — used in data centers; Type 2 (hosted) runs on top of a host OS (VirtualBox, VMware Workstation) — used on dev laptops.
- *Follow-up: Why is a VM "encapsulated"?* → It's stored as files, so you can snapshot, copy, move, and back it up easily.

**Q2. Why can't we just run many apps on one physical server?**
**A.** Resource contention (noisy neighbour), dependency/compatibility conflicts, and a shared security blast radius — plus resource wastage and high cost.
- *Follow-up: How do VMs solve this?* → Strong isolation per VM; each gets its own OS and allocated resources.
- *Follow-up: What new problem do VMs introduce?* → Each VM carries a full Guest OS → heavy, slow to boot, large images, OS licensing costs.

### B. Containers & Docker

**Q3. What is the difference between a VM and a container?**
**A.** VMs virtualize **hardware** and each runs a full Guest OS (heavy, GBs, boots in minutes). Containers virtualize the **OS** and **share the host kernel** (lightweight, MBs, start in seconds). VMs give stronger isolation; containers give better density, portability, and speed.
- *Follow-up: Can you run containers inside a VM?* → Yes — very common in the cloud; managed K8s nodes are usually VMs running containers.
- *Follow-up: When would you still prefer a VM?* → Strong isolation needs, different OS kernels, legacy apps, regulatory/security boundaries.

**Q4. How does Docker achieve isolation without a hypervisor?**
**A.** Linux kernel features: **namespaces** (isolate what a container can *see* — PIDs, network, mounts, etc.) and **cgroups** (limit what it can *use* — CPU, memory, I/O).
- *Follow-up: Name some namespace types.* → pid, net, mnt, uts, ipc, user.
- *Follow-up: What do cgroups prevent?* → One container hogging all resources (ensures fair sharing & stability).

**Q5. Explain Dockerfile vs Image vs Container.**
**A.** Dockerfile = the **recipe** (build instructions). Image = the **read-only template** built from it. Container = a **running instance** of an image. Flow: Dockerfile → build → Image → run → Container.
- *Follow-up: Difference between `RUN`, `CMD`, and `ENTRYPOINT`?* → `RUN` executes at **build** time (layers into the image); `CMD` sets the **default** runtime command (overridable); `ENTRYPOINT` sets a fixed executable, with `CMD`/args appended.
- *Follow-up: Difference between `COPY` and `ADD`?* → Both copy files; `ADD` also handles remote URLs and auto-extracts tar archives. Prefer `COPY` for clarity.
- *Follow-up: What is a Docker layer and why order matters?* → Each instruction creates a cached layer; putting rarely-changing steps (deps install) first speeds rebuilds.

**Q6. What does `docker run -d -p 80:8080 myapp` do?**
**A.** Runs `myapp` **detached** (background), mapping **host port 80** to **container port 8080**, so external traffic on 80 reaches the app on 8080.
- *Follow-up: What's the difference between `EXPOSE` and `-p`?* → `EXPOSE` only documents the port; `-p` actually publishes/maps it to the host.

**Q7. What is the difference between an image and a container, in terms of state?**
**A.** An image is **immutable/read-only**; a container adds a thin **writable layer** on top. Data written inside a container is lost when it's removed — unless you use **volumes** or **bind mounts** for persistence.
- *Follow-up: How do you persist data?* → Named **volumes** (`-v`) or bind mounts; for DBs, mount a volume.

### C. Registry & Deployment

**Q8. What is a container registry? Name a few.**
**A.** A centralized store for images supporting versioning, distribution, and access control. Examples: Docker Hub, Amazon ECR, Google GCR/Artifact Registry, Azure ACR, GHCR.
- *Follow-up: Why avoid the `latest` tag in production?* → It's mutable/ambiguous → non-reproducible deploys and hard rollbacks. Use explicit version tags.
- *Follow-up: Public vs private registry?* → Private adds authentication/access control for proprietary images.

**Q9. Walk me through deploying a container to AWS EC2.**
**A.** Build & tag the image → push to a registry → launch an EC2 instance (AMI, instance type, storage, security group allowing SSH 22 + app port, key pair) → SSH in → install Docker → `docker pull` → `docker run -d -p 80:8080 image`. Security group + public IP makes it internet-reachable.
- *Follow-up: What's a security group?* → A virtual firewall controlling inbound/outbound traffic to the instance.
- *Follow-up: Why is the `.pem` key important?* → It's your SSH credential; can't be re-downloaded; losing it locks you out.

### D. Orchestration

**Q10. What is container orchestration and why do we need it?**
**A.** Automated management of many containers: scheduling, scaling, networking, health checks/self-healing, and rolling updates. Needed once you go beyond a few containers (HA single service or microservices).
- *Follow-up: Name orchestration tools.* → Kubernetes, Docker Swarm, ECS/EKS, GKE, AKS, Nomad.
- *Follow-up: What is a Pod in Kubernetes?* → The smallest deployable unit — one or more containers sharing network/storage.
- *Follow-up: How does a rolling update give zero downtime?* → New containers are brought up and verified healthy while old ones are gradually drained/removed.
- *Follow-up: What is self-healing?* → The orchestrator restarts/reschedules failed containers automatically to match the desired state.

**Q11. What's the difference between scaling up and scaling out?**
**A.** Scale **up** (vertical) = bigger machine (more CPU/RAM). Scale **out** (horizontal) = more instances/containers. Orchestration favors scaling **out**.

### E. Architecture

**Q12. Monolithic vs Microservices — compare.**
**A.** Monolith = single codebase/deployment, simple, fast in-process calls, but hard to scale selectively and risky (one bug can crash all). Microservices = small independent services, independently scalable/deployable, polyglot, resilient — but add distributed-system complexity (networking, data consistency, observability).
- *Follow-up: When would you choose a monolith?* → Small app/team, early-stage product, simple domain — start monolith, split later.
- *Follow-up: How do microservices communicate?* → APIs (REST/gRPC), message brokers (Kafka/RabbitMQ/SQS), service mesh (Istio).
- *Follow-up: Biggest challenge in microservices?* → Data consistency across services and distributed debugging/tracing.
- *Follow-up: What is the "database per service" pattern?* → Each service owns its data store; no shared DB → loose coupling, but cross-service queries/transactions get harder (use eventual consistency / sagas).

**Q13. How do containers relate to microservices?**
**A.** Each microservice ships in its own container → isolation, portability, independent scaling, easy deploy, fault tolerance. Containers + Kubernetes are the standard backbone for microservices.

**Q14. (ML-focused) How are Docker/microservices used in machine learning?**
**A.** Containers pin exact library/runtime versions for **reproducibility**; models are served as containerized API endpoints; multiple models run as independent microservices, each scaled by its own traffic, enabling A/B tests and canary rollouts.

### F. Rapid-fire conceptual

**Q15. Why are containers more portable than VMs?**
**A.** They're small, kernel-sharing, and bundle their own dependencies, so the same image runs identically anywhere a container runtime exists — no full-OS baggage.

**Q16. What does "it works on my machine" have to do with Docker?**
**A.** Containers package the app *with* its environment, eliminating environment drift between dev/test/prod — so it works the same everywhere.

**Q17. What is the noisy-neighbour problem and how is it mitigated?**
**A.** One workload consuming shared resources degrades others. Mitigated by isolation (VMs/containers) + resource limits (cgroups / K8s requests & limits).

---

## 11. Cheat Sheet
### Quick revision

| Concept | One-liner |
|--------|-----------|
| **VM** | Full OS emulation via hypervisor — isolated but heavy. |
| **Container** | Shares host kernel — lightweight, portable, fast. |
| **Namespaces** | Isolation — what a container can *see*. |
| **cgroups** | Limits — how much a container can *use*. |
| **Dockerfile** | Recipe to build an image. |
| **Image** | Read-only template. |
| **Container** | Running instance of an image. |
| **Registry** | Centralized image store (Docker Hub, ECR, GCR). |
| **Orchestration** | Auto manage/scale/heal many containers (Kubernetes). |
| **Monolith** | One unit — simple but rigid. |
| **Microservices** | Small independent services — scalable but complex. |

**Essential Docker commands**
```bash
docker build -t myapp:latest .          # build image
docker images                           # list images
docker run -d -p 80:8080 myapp:latest   # run container
docker ps                               # list running containers
docker login                            # auth to registry
docker tag myapp:latest registry/myapp  # tag for registry
docker push registry/myapp:latest       # push image
docker pull registry/myapp:latest       # pull image
docker stop <id> / docker rm <id>       # stop / remove container
docker logs <id>                        # view container logs
docker exec -it <id> bash               # shell into a container
```

---

*End of notes — Session 30: DevOps Fundamentals.*
