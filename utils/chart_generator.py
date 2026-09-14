import io
import matplotlib.pyplot as plt
import matplotlib
from typing import List, Dict

# Use a non-interactive backend so it doesn't try to open windows
matplotlib.use('Agg')

def generate_document_chart(base_class: str, docs: List[Dict]) -> io.BytesIO:
    """
    Generate a bar chart for document quantities
    
    Args:
        base_class: Khối lớp (e.g. '6', '7')
        docs: List of dicts with 'chapter' and 'remaining' keys
        
    Returns:
        io.BytesIO containing the PNG image
    """
    # X and Y data
    chapters = [f"Chương {doc['chapter']}" for doc in docs]
    counts = [doc['remaining'] for doc in docs]
    
    # Create figure
    plt.figure(figsize=(10, 6))
    
    # Create bar chart
    bars = plt.bar(chapters, counts, color='#4CAF50')
    
    # Add values on top of bars
    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2, yval + 0.2, int(yval), 
                 ha='center', va='bottom', fontweight='bold')
                 
    # Formatting
    plt.title(f'Thống Kê Tài Liệu Còn Lại - Khối {base_class}', fontsize=16, fontweight='bold', pad=20)
    plt.xlabel('Chương', fontsize=12)
    plt.ylabel('Số lượng còn', fontsize=12)
    
    # Rotate x-axis labels if there are many chapters
    if len(chapters) > 6:
        plt.xticks(rotation=45, ha='right')
        
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()
    
    # Save to buffer
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=100)
    plt.close()
    
    buf.seek(0)
    return buf
