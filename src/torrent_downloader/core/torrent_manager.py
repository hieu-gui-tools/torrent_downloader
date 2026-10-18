import libtorrent as lt
import time
import os
import json
from pathlib import Path

class TorrentManager:
    def __init__(self, download_dir="downloads", data_dir="data"):
        self.data_dir = Path(data_dir).resolve()
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.fastresume_dir = self.data_dir / "fastresume"
        self.fastresume_dir.mkdir(parents=True, exist_ok=True)
        
        self.session_file = self.data_dir / "torrents.json"
        self.settings_file = self.data_dir / "settings.json"
        
        # Load user settings or initialize defaults
        self.settings = self.load_settings(default_download_dir=download_dir)
        self.download_dir = Path(self.settings.get("download_dir", download_dir)).resolve()
        self.download_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize libtorrent session with speed optimizations
        self.session = lt.session({'listen_interfaces': '0.0.0.0:6881'})
        
        settings = {
            'active_downloads': 20,
            'active_seeds': 20,
            'active_limit': 40,
            'connections_limit': 1500,
            'download_rate_limit': 0,  # unlimited
            'upload_rate_limit': 0,    # unlimited
            'alert_mask': (lt.alert_category.status | 
                           lt.alert_category.storage | 
                           lt.alert_category.error)
        }
        self.session.apply_settings(settings)
        
        # Mapping: info_hash (str) -> handle
        self.handles = {}
        # Mapping: info_hash (str) -> metadata dict
        self.torrents_meta = {}
        
        # Load saved session
        self.load_session()

    def load_settings(self, default_download_dir="downloads"):
        default_settings = {
            "download_dir": str(Path(default_download_dir).resolve()),
            "minimize_to_tray": True,
            "close_to_tray": True
        }
        if not self.settings_file.exists():
            return default_settings
        try:
            with open(self.settings_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    default_settings.update(data)
        except Exception as e:
            print(f"[WARN] Could not read settings file: {e}")
        return default_settings

    def save_settings(self):
        try:
            temp_file = self.settings_file.with_suffix(".tmp")
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(self.settings, f, indent=2, ensure_ascii=False)
            temp_file.replace(self.settings_file)
        except Exception as e:
            print(f"[ERROR] Failed to save settings: {e}")

    def set_download_dir(self, new_dir):
        path = Path(new_dir).resolve()
        path.mkdir(parents=True, exist_ok=True)
        self.download_dir = path
        self.settings["download_dir"] = str(path)
        self.save_settings()

    def update_settings(self, new_settings):
        if "download_dir" in new_settings:
            path = Path(new_settings["download_dir"]).resolve()
            path.mkdir(parents=True, exist_ok=True)
            self.download_dir = path
            new_settings["download_dir"] = str(path)
        self.settings.update(new_settings)
        self.save_settings()

    def get_info_hash_str(self, handle_or_params):
        try:
            if hasattr(handle_or_params, 'info_hashes'):
                ih = handle_or_params.info_hashes
                return str(ih.v1 if hasattr(ih, 'v1') else ih)
            elif hasattr(handle_or_params, 'info_hash'):
                return str(handle_or_params.info_hash())
        except Exception:
            pass
        return None

    def add_magnet_link(self, magnet_uri, save_path=None):
        target_save_path = str(Path(save_path).resolve()) if save_path else str(self.download_dir)
        Path(target_save_path).mkdir(parents=True, exist_ok=True)
        params = lt.parse_magnet_uri(magnet_uri)
        params.save_path = target_save_path
        
        info_hash = self.get_info_hash_str(params)
        if not info_hash:
            info_hash = str(time.time())

        # If already added, return existing handle
        if info_hash in self.handles:
            return self.handles[info_hash], info_hash

        # Check for existing fastresume data
        fastresume_file = self.fastresume_dir / f"{info_hash}.fastresume"
        handle = None
        if fastresume_file.exists():
            try:
                with open(fastresume_file, "rb") as f:
                    resume_bytes = f.read()
                resume_params = lt.read_resume_data(resume_bytes)
                resume_params.save_path = target_save_path
                handle = self.session.add_torrent(resume_params)
            except Exception as e:
                print(f"[WARN] Failed to load fastresume for {info_hash}: {e}")
                handle = None

        if handle is None:
            handle = self.session.add_torrent(params)

        name = params.name if params.name else "Downloading metadata..."

        self.handles[info_hash] = handle
        self.torrents_meta[info_hash] = {
            'info_hash': info_hash,
            'magnet_uri': magnet_uri,
            'name': name,
            'save_path': target_save_path,
            'added_time': time.time(),
            'is_paused': False
        }

        self.save_session()
        return handle, info_hash

    def load_session(self):
        if not self.session_file.exists():
            return

        try:
            with open(self.session_file, "r", encoding="utf-8") as f:
                saved_items = json.load(f)
        except Exception as e:
            print(f"[WARN] Could not read session file: {e}")
            return

        for item in saved_items:
            info_hash = item.get('info_hash')
            magnet_uri = item.get('magnet_uri')
            save_path = item.get('save_path', str(self.download_dir))
            fastresume_file = self.fastresume_dir / f"{info_hash}.fastresume"

            handle = None
            if fastresume_file.exists():
                try:
                    with open(fastresume_file, "rb") as f:
                        resume_bytes = f.read()
                    params = lt.read_resume_data(resume_bytes)
                    params.save_path = save_path
                    handle = self.session.add_torrent(params)
                except Exception as e:
                    print(f"[WARN] Failed to resume from fastresume for {info_hash}: {e}")
                    handle = None

            if handle is None and magnet_uri:
                try:
                    params = lt.parse_magnet_uri(magnet_uri)
                    params.save_path = save_path
                    handle = self.session.add_torrent(params)
                except Exception as e:
                    print(f"[ERROR] Failed to restore torrent {magnet_uri}: {e}")
                    continue

            if handle:
                # If was paused
                if item.get('is_paused', False):
                    handle.pause()

                self.handles[info_hash] = handle
                self.torrents_meta[info_hash] = item

    def save_session(self):
        try:
            items = list(self.torrents_meta.values())
            temp_file = self.session_file.with_suffix(".tmp")
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(items, f, indent=2, ensure_ascii=False)
            temp_file.replace(self.session_file)
        except Exception as e:
            print(f"[ERROR] Failed to save session: {e}")

    def process_alerts(self):
        alerts = self.session.pop_alerts()
        for alert in alerts:
            # When metadata is fetched from peers
            if isinstance(alert, lt.metadata_received_alert):
                h = alert.handle
                if h.is_valid():
                    ih = self.get_info_hash_str(h)
                    if ih and ih in self.torrents_meta:
                        status = h.status()
                        self.torrents_meta[ih]['name'] = status.name
                        self.save_session()
                    # Request fastresume generation
                    try:
                        h.save_resume_data()
                    except Exception:
                        pass

            # When fastresume data is generated
            elif isinstance(alert, lt.save_resume_data_alert):
                h = alert.handle
                if h.is_valid():
                    ih = self.get_info_hash_str(h)
                    if ih:
                        try:
                            entry = lt.write_resume_data(alert.params)
                            bencoded = lt.bencode(entry)
                            target_file = self.fastresume_dir / f"{ih}.fastresume"
                            with open(target_file, "wb") as f:
                                f.write(bencoded)
                        except Exception as e:
                            print(f"[ERROR] Failed writing fastresume for {ih}: {e}")

            # When torrent finishes download
            elif isinstance(alert, lt.torrent_finished_alert):
                h = alert.handle
                if h.is_valid():
                    try:
                        h.save_resume_data()
                    except Exception:
                        pass

    def request_save_resume_data(self):
        for ih, handle in self.handles.items():
            if handle.is_valid():
                try:
                    handle.save_resume_data()
                except Exception:
                    pass

    def pause_torrent(self, info_hash):
        if info_hash in self.handles:
            h = self.handles[info_hash]
            if h.is_valid():
                h.pause()
                if info_hash in self.torrents_meta:
                    self.torrents_meta[info_hash]['is_paused'] = True
                    self.save_session()

    def resume_torrent(self, info_hash):
        if info_hash in self.handles:
            h = self.handles[info_hash]
            if h.is_valid():
                h.resume()
                if info_hash in self.torrents_meta:
                    self.torrents_meta[info_hash]['is_paused'] = False
                    self.save_session()

    def remove_torrent(self, info_hash, delete_files=False):
        if info_hash in self.handles:
            h = self.handles[info_hash]
            if h.is_valid():
                try:
                    if delete_files:
                        self.session.remove_torrent(h, lt.options_t.delete_files)
                    else:
                        self.session.remove_torrent(h)
                except Exception as e:
                    print(f"[WARN] Error removing torrent handle: {e}")

            del self.handles[info_hash]

            if info_hash in self.torrents_meta:
                del self.torrents_meta[info_hash]

            fastresume_file = self.fastresume_dir / f"{info_hash}.fastresume"
            if fastresume_file.exists():
                try:
                    fastresume_file.unlink()
                except Exception:
                    pass

            self.save_session()

    def get_torrents_status(self):
        self.process_alerts()
        status_list = []

        for info_hash, handle in list(self.handles.items()):
            if not handle.is_valid():
                continue

            s = handle.status()
            meta = self.torrents_meta.get(info_hash, {})

            state_names = [
                'queued', 'checking', 'downloading metadata',
                'downloading', 'finished', 'seeding', 'allocating', 'checking fastresume'
            ]
            state_str = state_names[s.state] if s.state < len(state_names) else 'unknown'

            if s.paused:
                state_str = 'paused'

            # Name determination
            name = meta.get('name', 'Unknown')
            if handle.has_metadata():
                name = s.name
                if meta.get('name') != name:
                    meta['name'] = name

            info = {
                'info_hash': info_hash,
                'name': name,
                'progress': s.progress * 100,
                'download_rate': s.download_rate,
                'upload_rate': s.upload_rate,
                'state': state_str,
                'num_peers': s.num_peers,
                'total_wanted': s.total_wanted,
                'total_done': s.total_done,
                'save_path': meta.get('save_path', str(self.download_dir)),
                'magnet_uri': meta.get('magnet_uri', ''),
                'is_paused': s.paused
            }
            status_list.append((info_hash, info))

        return status_list
