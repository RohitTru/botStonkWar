import os
import re

STRATEGY_FILES = [
    'short_term.py',
    'consensus.py',
    'reversal.py',
    'obscure.py',
    'momentum.py',
    'price_confirmation.py',
    'mean_reversion.py',
    'volume_spike.py',
    'news_breakout.py',
    'sentiment_divergence.py'
]

def update_strategy_file(filepath):
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Update imports if needed
    if 'from datetime import datetime' not in content:
        content = 'from datetime import datetime\n' + content
    
    # Update class definition to ensure proper inheritance
    class_pattern = r'class (\w+)\(BaseStrategy\):'
    for match in re.finditer(class_pattern, content):
        class_name = match.group(1)
        # Find the __init__ method
        init_pattern = r'def __init__\(self[^)]*\):(?:[^#]|#[^\n]*\n)*?super\(\)'
        if not re.search(init_pattern, content):
            # Add proper super() call if missing
            init_replacement = f'''def __init__(self, *args, **kwargs):
        super().__init__(
            name="{class_name.lower()}",
            description=self.__doc__.strip() if self.__doc__ else "No description available"
        )'''
            content = re.sub(r'def __init__\([^)]*\):[^\n]*\n', init_replacement + '\n', content)
    
    # Remove any update_last_run references
    content = re.sub(r'\s+self\.update_last_run\(\)\n', '\n', content)
    
    with open(filepath, 'w') as f:
        f.write(content)

def main():
    # Get the directory containing this script
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    for filename in STRATEGY_FILES:
        filepath = os.path.join(current_dir, filename)
        if os.path.exists(filepath):
            print(f"Updating {filename}...")
            update_strategy_file(filepath)
        else:
            print(f"Warning: {filename} not found")

if __name__ == '__main__':
    main() 