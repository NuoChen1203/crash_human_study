


import streamlit as st
import os
import json
import pandas as pd
from datetime import datetime
from typing import Iterator, Tuple, Dict, Any, List, Optional
import random, glob

# Define types for clarity
ImagePair = Tuple[str, str, Dict[str, Any]]  # (image1_path, image2_path, metadata)
Preference = Dict[str, Any]  # Will contain preference data

class ImagePairIterator:
    """Mock iterator for demonstration purposes.
    In a real implementation, this would be replaced with your actual img_pairs iterator."""
    
    @staticmethod
    def _generate_pairs(total: int,
                        dirs: List[str],
                        postfix,
                        seed: int,
                        same_idx) -> List[ImagePair]:
        """Generate pairs of image paths with metadata."""
        if seed is not None:
            random.seed(seed)
        else:
            random.seed()
        
        pairs = []
        if not same_idx:
            # A/3.jpg, B/5.jpg style
            images = {
                dir: glob.glob(os.path.join(dir, f"*{postfix}"))
                for dir in dirs
            }

            for i in range(total):
                dir1, dir2 = random.sample(dirs, 2)
                img1 = random.choice(images[dir1])
                img2 = random.choice(images[dir2])
                metadata = {"pair_id": i, "A_dir": dir1, "B_dir": dir2}
                pairs.append((img1, img2, metadata))
            return pairs
        else:
            # A/3.jpg, B/3.jpg style
            image_names = glob.glob(os.path.join(dirs[0], f"*{postfix}"))
            image_names = [os.path.basename(name) for name in image_names]
            for i in range(total):
                img_name = random.choice(image_names)
                dir1, dir2 = random.sample(dirs, 2)
                img1 = os.path.join(dir1, img_name)
                img2 = os.path.join(dir2, img_name)
                metadata = {"pair_id": i, "A_dir": dir1, "B_dir": dir2}
                pairs.append((img1, img2, metadata))
            return pairs

    def __init__(self, config_file):
        with open(config_file, 'r') as f:
            self.cfg = json.load(f)
        
        self.pairs = ImagePairIterator._generate_pairs(
            total = self.cfg["total_pairs"],
            dirs  = self.cfg["img_dirs"],
            postfix = self.cfg["img_postfix"],
            seed  = self.cfg["rand_seed"],
            same_idx = self.cfg["parallel_sample"])
        self.index = 0
    
    def __iter__(self):
        self.index = 0
        return self
    
    def __next__(self) -> ImagePair:
        if self.index < len(self.pairs):
            pair = self.pairs[self.index]
            self.index += 1
            return pair
        raise StopIteration


class PreferenceManager:
    """Manages recording and loading of user preferences."""
    
    def __init__(self, save_path):
        self.save_path = save_path
        self.preferences: List[Preference] = self._load_preferences()
    
    def _load_preferences(self) -> List[Preference]:
        """Load preferences from file if it exists."""
        if os.path.exists(self.save_path):
            try:
                with open(self.save_path, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                st.error(f"Error loading preferences from {self.save_path}. Starting with empty preferences.")
                return []
        return []
    
    def save_preferences(self):
        """Save preferences to file."""
        with open(self.save_path, 'w') as f:
            json.dump(self.preferences, f, indent=2)
    
    def add_preference(self, image_pair: ImagePair, choice: str):
        """Add a new preference."""
        img1, img2, metadata = image_pair
        preference = {
            "timestamp": datetime.now().isoformat(),
            "A": img1,
            "B": img2,
            "choice": choice,
            "metadata": metadata
        }
        # Check if this pair has already been judged
        pair_id = metadata.get("pair_id")
        for i, pref in enumerate(self.preferences):
            if pref["metadata"].get("pair_id") == pair_id:
                # Update existing preference
                self.preferences[i] = preference
                self.save_preferences()
                return
        
        # Add new preference
        self.preferences.append(preference)
        self.save_preferences()
    
    def get_preference(self, pair_id) -> Optional[Preference]:
        """Get preference for a specific pair_id."""
        for pref in self.preferences:
            if pref["metadata"].get("pair_id") == pair_id:
                return pref
        return None


def getPerferenceManager():
    cur_timestamp  = datetime.now().strftime("%Y%m%d-%H%M%S")
    save_path = f"result_{cur_timestamp}.json"
    return PreferenceManager(save_path)

def main():
    st.set_page_config(
        page_title="Image Preference Selection",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    
    # Apply custom CSS for a stylish appearance
    st.markdown("""
    <style>
        .main {
            background-color: #f7f7f8;
        }
        .stButton button {
            background-color: #10a37f;
            color: white;
            border-radius: 4px;
            border: none;
            padding: 0.5rem 1rem;
            font-weight: bold;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 1rem 0;
        }
        .stButton button:disabled {
            background-color: #cccccc;
            color: #666666;
            cursor: not-allowed;
        }
        .image-container {
            display: flex;
            justify-content: space-around;
            align-items: center;
            margin-bottom: 2rem;
        }
        .image-card {
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            transition: transform 0.3s;
        }
        .image-card:hover {
            transform: translateY(-5px);
        }
        .preference-header {
            font-size: 1.5rem;
            font-weight: bold;
            margin-bottom: 1rem;
            color: #444654;
        }
        .choice-container {
            display: flex;
            justify-content: space-around;
            margin-top: 1rem;
        }
        .progress-container {
            margin-top: 2rem;
            margin-bottom: 2rem;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Initialize session state
    if 'current_index' not in st.session_state:
        st.session_state.current_index = 0
    if 'img_pairs' not in st.session_state:
        # In a real implementation, img_pairs would be provided as an argument
        st.session_state.img_pairs = list(ImagePairIterator("config.json"))
    if 'preference_manager' not in st.session_state:
        st.session_state.preference_manager = getPerferenceManager()
    if 'current_selection' not in st.session_state:
        st.session_state.current_selection = None
    
    # Header
    st.markdown("<h1 style='text-align: center; color: #444654;'>Image Preference Selection</h1>", unsafe_allow_html=True)
    
    # Progress bar
    total_pairs = len(st.session_state.img_pairs)
    # Get current image pair
    if st.session_state.current_index < len(st.session_state.img_pairs):
        progress = (st.session_state.current_index + 1) / total_pairs
        st.markdown("<div class='progress-container'>", unsafe_allow_html=True)
        st.progress(progress)
        st.markdown(f"<p style='text-align: center;'>Pair {st.session_state.current_index + 1} of {total_pairs}</p>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        current_pair = st.session_state.img_pairs[st.session_state.current_index]
        img1, img2, metadata = current_pair
        pair_id = metadata.get("pair_id")
        
        # Check if this pair already has a preference
        existing_preference = st.session_state.preference_manager.get_preference(pair_id)
        if existing_preference and st.session_state.current_selection is None:
            st.session_state.current_selection = existing_preference.get("choice")
        
        # Display image pair
        st.markdown("<div class='preference-header'>Which video seems more physically reasonable?</div>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        
        # Function to handle preference selection
        def select_preference(choice):
            st.session_state.current_selection = choice
            st.session_state.preference_manager.add_preference(current_pair, choice)
        
        with col1:
            st.markdown(f"<div class='image-card'>", unsafe_allow_html=True)
            st.header("Video A")
            st.video(img1, loop=True)
            # st.image(img1, caption="Image A", use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)
            if st.button("Prefer A", key="btnA", 
                        help="Click to select Image A as your preference"):
                select_preference("A")
                st.rerun()
            
        with col2:
            st.markdown(f"<div class='image-card'>", unsafe_allow_html=True)
            st.header("Video B")
            st.video(img2, loop=True)
            # st.image(img2, caption="Image B", use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)
            if st.button("Prefer B", key="btnB", 
                        help="Click to select Image B as your preference"):
                select_preference("B")
                st.rerun()
        
        # Show current selection if it exists
        cur_selected = st.session_state.current_selection or "None"
        st.markdown(f"<p style='text-align: center; font-weight: bold; color: #10a37f;'>Your current selection: {cur_selected}</p>", unsafe_allow_html=True)
        
        # Navigation buttons
        col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
        with col1:
            # if st.session_state.current_index > 0:
            #     if st.button("← Previous", help="Go back to the previous image pair"):
            #         st.session_state.current_index -= 1
            #         st.session_state.current_selection = None
            #         st.rerun()
            prev_button = st.button(
                "← Previous", 
                help="Go back to the previous image pair",
                disabled=st.session_state.current_index == 0,
                key="prev_button",
                use_container_width=True
            )
            if prev_button:
                st.session_state.current_index -= 1
                st.session_state.current_selection = None
                st.rerun()
        with col2:
            if st.button("Play all videos", use_container_width=True):
                st.components.v1.html(
                    """<script>
                    let videos = parent.document.querySelectorAll("video");
                    videos.forEach(v => {
                        v.play();
                    })
                    </script>""", 
                    width=0, height=0
                )
        with col3:
            if st.button("Pause all videos", use_container_width=True):
                st.components.v1.html(
                    """<script>
                    let videos = parent.document.querySelectorAll("video");
                    videos.forEach(v => {
                        v.pause();
                    })
                    </script>""", 
                    width=0, height=0
                )

        with col4:
            # Next button - only created if a selection has been made, otherwise it's disabled
            next_button = st.button(
                "Next →", 
                help="Finish this pair and move to the next one",
                disabled=not st.session_state.current_selection,
                key="next_button",
                use_container_width=True
            )
            
            if next_button and st.session_state.current_selection:
                st.session_state.current_index += 1
                st.session_state.current_selection = None
                st.rerun()
                
            # Add helper text if no selection made
            if next_button and not st.session_state.current_selection:
                st.markdown("<p style='text-align: center; font-size: 0.9rem; color: #666666; margin-top: 0.5rem;'>Please select a preference to continue</p>", unsafe_allow_html=True)
    else:
        # All pairs have been viewed
        st.success("🎉 You've completed all image pairs!")
        
        # Display results
        st.markdown("<h2>Your Preferences</h2>", unsafe_allow_html=True)
        preferences = st.session_state.preference_manager.preferences
        
        if preferences:
            # Convert to DataFrame for better display
            df = pd.DataFrame(preferences)
            
            st.dataframe(df)
            
            # Download button
            csv = df.to_csv(index=False)
            st.download_button(
                label="Download Results as CSV",
                data=csv,
                file_name="image_preferences.csv",
                mime="text/csv",
            )
        else:
            st.info("No preferences recorded yet.")
        
        # Restart button
        if st.button("New Round", help="New result.json"):
            st.session_state.current_index = 0
            st.session_state.current_selection = None
            st.session_state.preference_manager = getPerferenceManager()
            st.rerun()
    
    # Show sidebar with information
    with st.sidebar:
        st.markdown("## About")
        st.markdown("""
        This application lets you select your preferred image from pairs of images.
        
        - Select your preference by clicking "Prefer A" or "Prefer B"
        - You must make a selection before proceeding to the next pair
        - You can go back to revise previous selections
        - Your preferences are automatically saved
        """)
        
        # Show metadata of current pair
        if st.session_state.current_index < len(st.session_state.img_pairs):
            current_pair = st.session_state.img_pairs[st.session_state.current_index]
            _, _, metadata = current_pair
            
            st.markdown("## Current Pair Metadata")
            st.json(metadata)


if __name__ == "__main__":
    main()