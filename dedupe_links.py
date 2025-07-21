#!/usr/bin/env python3

def deduplicate_links(input_file, output_file):
    """
    Remove duplicate links from a file, preserving order of first occurrence.
    Also removes empty lines.
    """
    seen_links = set()
    unique_links = []
    
    with open(input_file, 'r', encoding='utf-8') as f:
        for line in f:
            link = line.strip()
            # Skip empty lines
            if not link:
                continue
            # Add link if not seen before
            if link not in seen_links:
                seen_links.add(link)
                unique_links.append(link)
    
    # Write deduplicated links to output file
    with open(output_file, 'w', encoding='utf-8') as f:
        for link in unique_links:
            f.write(link + '\n')
    
    print(f"Original links: {len(seen_links) + (sum(1 for line in open(input_file) if not line.strip()))}")
    print(f"Unique links: {len(unique_links)}")
    print(f"Duplicates removed: {len(seen_links) - len(unique_links) if len(seen_links) > len(unique_links) else 0}")

if __name__ == "__main__":
    deduplicate_links('links.txt', 'links_unique.txt')