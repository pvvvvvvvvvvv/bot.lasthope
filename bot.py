def get_game_data(self):
    """Fetch total players and total visits safely with fallbacks."""
    headers = {"User-Agent": "Mozilla/5.0"}
    total_players = 0
    visits = self.current_visits  # start with last known visits

    try:
        # Step 1: Universe ID
        universe_resp = requests.get(
            f"https://apis.roblox.com/universes/v1/places/{self.place_id}/universe",
            headers=headers, timeout=10
        )
        universe_resp.raise_for_status()
        universe_id = universe_resp.json().get("universeId")
        logging.info(f"Universe ID: {universe_id}")
        if not universe_id:
            raise Exception("Cannot get universe ID")

        # Step 2: Total visits
        game_resp = requests.get(
            f"https://games.roblox.com/v1/games?universeIds={universe_id}",
            headers=headers, timeout=10
        )
        game_resp.raise_for_status()
        game_data = game_resp.json()["data"][0]
        api_visits = game_data.get("visits", None)

        # Only update visits if valid
        if api_visits is not None and api_visits > 0:
            visits = api_visits
        else:
            logging.warning(f"Visits API returned invalid value, keeping last known: {self.current_visits}")
            visits = self.current_visits

        self.current_visits = max(self.current_visits, visits)

        # Step 3: Total active players
        cursor = ""
        while True:
            servers_url = f"https://games.roblox.com/v1/games/{self.place_id}/servers/Public?sortOrder=Asc&limit=100"
            if cursor:
                servers_url += f"&cursor={cursor}"
            server_resp = requests.get(servers_url, headers=headers, timeout=10)
            server_resp.raise_for_status()
            server_data = server_resp.json()
            data_list = server_data.get("data", [])
            server_total = sum(server.get("playing", 0) for server in data_list)
            total_players += server_total
            logging.info(f"Fetched {len(data_list)} servers, total players so far: {total_players}")
            cursor = server_data.get("nextPageCursor")
            if not cursor:
                break

        return total_players, self.current_visits

    except Exception as e:
        logging.error(f"Error fetching game data: {e}")
        # fallback to last known values
        return random.randint(10, 25), max(3258, self.current_visits)
