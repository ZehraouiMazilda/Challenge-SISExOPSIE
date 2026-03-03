# Partie OPSIE - Challenge SISE-OPSIE 2026

## 1) Objectif de cette partie
Cette partie couvre uniquement le scope OPSIE (cybersecurite / journalisation), sans la partie webapp ou machine learning.

Le but est de mettre en place une chaine complete:

- Firewall avec `iptables` + `ulogd2`
- Envoi des logs vers un serveur central `syslog-ng`
- Stockage des logs dans `MySQL` (+ consultation via `phpMyAdmin`)
- Envoi des memes logs vers ELK (`Logstash -> Elasticsearch -> Kibana`)
- Dashboard Kibana pour l'analyse

## 2) Architecture retenue
Flux principal:

`iptables -> ulogd2 -> rsyslog -> syslog-ng -> (fichier + MySQL + Logstash) -> Elasticsearch -> Kibana`

Services Docker utilises:

- `opsie-fw` (firewall)
- `opsie-syslog` (syslog-ng)
- `opsie-db` (MySQL)
- `opsie-pma` (phpMyAdmin)
- `opsie-logstash`
- `opsie-elasticsearch`
- `opsie-kibana`

## 3) Champs transformes 
Les champs extraits et normalises sont:

- `datetime` (YYYY-MM-DD HH:MM:SS)
- `ipsrc`
- `ipdst`
- `proto` (TCP/UDP)
- `dstport`
- `action` (Permit / Deny)
- `policyid` (cleanup = 999)
- `interface_in`
- `interface_out`

## Installation
Cette partie a ete testee sous `WSL (Kali)` avec Docker Desktop.

### 1) Prerequis Windows

- Installer **Docker Desktop** (et activer l'integration WSL).
- Verifier que ta distro Kali est bien active dans Docker Desktop:
  - `Settings -> Resources -> WSL Integration -> kali-linux`.

### 2) Prerequis WSL/Kali

Dans Kali:

```bash
sudo apt update
sudo apt install -y docker.io docker-compose-plugin curl
sudo usermod -aG docker $USER
newgrp docker
```

Verification:

```bash
docker --version
docker compose version
docker ps
```

Si `docker ps` ne repond pas, redemarre Docker Desktop puis relance ton terminal WSL.

### 3) Outils utiles pour les tests OPSIE

```bash
sudo apt install -y nmap netcat-openbsd hydra gobuster nikto hping3
```

## 5) Demarrage rapide
Depuis la racine du projet `Clean_solution`:

```bash
docker network create training_opsie 2>/dev/null || true
```

Lancer la stack syslog + DB + ELK:

```bash
cd 01-syslog-stack
docker compose up -d --build
docker compose ps
```

Construire et lancer le firewall:

```bash
cd ../02-ulog-iptables
docker build --no-cache -t opsie-ulog-iptables .
SYSLOG_IP=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' opsie-syslog)
docker rm -f opsie-fw 2>/dev/null || true
docker run -d --privileged --network training_opsie --name opsie-fw -e SYSLOG_SERVER_IP="$SYSLOG_IP" opsie-ulog-iptables
docker exec opsie-fw iptables -S | grep NFLOG
```

## 6) Verification rapide
Verifier logs fichier:

```bash
docker exec opsie-syslog tail -n 20 /var/log/firewall/firewall.log
```

Verifier DB:

```bash
docker exec opsie-db mysql -uroot -pmypass123 -e "USE Logs_fw; SELECT datetime,ipsrc,ipdst,proto,dstport,action,policyid,interface_in,interface_out FROM FW ORDER BY datetime DESC LIMIT 20;"
```

Verifier ELK:

```bash
curl -s http://localhost:9200/_cat/indices?v | grep opsie-firewall
curl -s http://localhost:9600/?pretty | grep '"status"'
curl -s -H 'kbn-xsrf: true' http://localhost:5601/api/status | head
```

## 7) Alimentation des donnees
Verifier d'abord les services demandes (20/21/22/23/80 accessibles, 3306 local only):

```bash
docker run --rm --network training_opsie nicolaka/netshoot sh -c '
for p in 20 21 22 23 80; do nc -zvw1 opsie-fw $p || true; done
nc -zvw1 opsie-fw 3306 || true
'
docker exec opsie-fw bash -lc "nc -zv 127.0.0.1 3306 || true"
```

Executer trafic licite + scenarios:

```bash
# Trafic licite 45 min
END=$((SECONDS+45*60))
while [ $SECONDS -lt $END ]; do
  docker run --rm --network training_opsie nicolaka/netshoot sh -c '
  for p in 20 21 22 23 80; do nc -zvw1 opsie-fw $p || true; done
  for p in 53 123 500; do echo test | nc -u -w1 opsie-fw $p || true; done
  '
  sleep 5
done

# Exemple de scan full TCP
nmap -Pn -p- opsie-fw -oA 03-traffic-attacks/outputs/nmap_full_tcp

# Exemple de scan furtif avec decoys
nmap -sS -Pn -D 10.0.0.1,192.168.4.1,172.156.2.26,192.168.1.0,10.10.1.101,89.89.56.2,28.12.15.20,10.172.11.2,194.25.56.2,172.5.2.8,ME opsie-fw

# Exemple de scan top 100 ports avec delai 1 seconde
nmap -Pn --top-ports 100 --scan-delay 1s opsie-fw
```

## 7.1) Scan zombie

```bash
# 0) Recuperer la cible firewall (IP docker)
TARGET_IP=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' opsie-fw)
echo "$TARGET_IP"

# 1) Decouvrir des hotes vivants (adaptation de CIDR a notre reseau)
sudo nmap -sn 159.84.146.0/16 -oN 03-traffic-attacks/outputs/zombie_live_hosts.txt

# 2) Detecter des zombies 
sudo nmap -Pn -p 80,443,22 --script ipidseq 159.84.146.0/24 -oN 03-traffic-attacks/outputs/zombie_candidates.txt

# 3) Choisir un candidat depuis zombie_candidates.txt
ZOMBIE_IP=159.84.146.Y

# 4) Lancer le scan idle (zombie) contre le firewall
sudo nmap -Pn -sI ${ZOMBIE_IP} ${TARGET_IP} -p- -oA 03-traffic-attacks/outputs/nmap_zombie_full

# 5) Variante top 100 ports
sudo nmap -Pn -sI ${ZOMBIE_IP} ${TARGET_IP} --top-ports 100 -oA 03-traffic-attacks/outputs/nmap_zombie_100p

# 6) Verifier les traces apres scan
docker exec opsie-syslog tail -n 100 /var/log/firewall/firewall.log
docker exec opsie-db mysql -uroot -pmypass123 -e "USE Logs_fw; SELECT datetime,ipsrc,ipdst,proto,dstport,action,policyid FROM FW ORDER BY datetime DESC LIMIT 100;"
```


## 8) Dashboard Kibana interactif 
URL Kibana: `http://localhost:5601`

Data view:

- Pattern: `opsie-firewall-*`
- Time field: `@timestamp`

Visualisations recommandees:

- `OPSIE - Total Events` (Metric / Count)
- `OPSIE - Deny Rate` (Metric / Formula)
- `OPSIE - Timeline Permit vs Deny` (Line)
- `OPSIE - Top Destination Ports` (Bar horizontal)
- `OPSIE - Top Source IP (Deny)` (Bar horizontal)
- `OPSIE - Protocol Distribution` (Pie/Donut)
- `OPSIE - Firewall Rules` (policyid + action)
- `OPSIE - Recent Events` (table)

Controls interactifs:

- `action.keyword`
- `proto.keyword`
- `policyid.keyword`
- `ipsrc.keyword`

## 9) Preuves pour le rendu
Exporter les preuves:

```bash
OUT="03-traffic-attacks/outputs/evidence_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$OUT"

docker exec opsie-fw iptables -S > "$OUT/iptables_rules.txt"
docker exec opsie-syslog tail -n 1000 /var/log/brut.log > "$OUT/brut_tail.txt"
docker exec opsie-syslog tail -n 1000 /var/log/firewall/firewall.log > "$OUT/firewall_tail.txt"
docker exec opsie-db mysql -uroot -pmypass123 -e "USE Logs_fw; SELECT datetime,ipsrc,ipdst,proto,dstport,action,policyid,interface_in,interface_out FROM FW ORDER BY datetime DESC LIMIT 1000;" > "$OUT/db_rows.txt"
docker ps > "$OUT/docker_ps.txt"
history > "$OUT/kali_history.txt"
```

Dossier produit:

- `03-traffic-attacks/outputs/evidence_*`

Contient notamment:

- regles iptables
- extraits logs syslog
- extraits SQL
- historique commandes
- statut conteneurs

## 10) Etat actuel
La chaine OPSIE est operationnelle et conforme sur les points principaux du sujet:

- ingestion logs OK
- transformation des champs OK
- stockage SQL OK
- ELK + Kibana OK
- dashboard realisable et presentable
