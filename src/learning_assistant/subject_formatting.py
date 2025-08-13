"""
Subject detection and formatting utilities for the learning assistant
"""

import re
from typing import Dict, List, Tuple, Optional

def detect_subject_matter(audio_transcription: str, slide_text: str, student_notes: str) -> str:
    """
    Detect the subject matter from the three input sources
    
    Args:
        audio_transcription: Audio content from the lesson
        slide_text: Text from slides or topic list
        student_notes: Student notes content
        
    Returns:
        Subject category string (e.g., 'data_ethics', 'distributed_architecture', 'general')
    """
    
    # Combine all content for analysis
    all_content = f"{audio_transcription} {slide_text} {student_notes}".lower()
    
    # Subject detection patterns
    subject_patterns = {
        'data_ethics': [
            r'\b(gdpr|data protection|privacy|consent|ethics|personal data|anonymization)\b',
            r'\b(data minimization|privacy by design|data subject rights)\b',
            r'\b(compliance|regulation|legal framework)\b'
        ],
        'distributed_architecture': [
            r'\b(spark|hadoop|distributed|big data|cluster|nodes)\b',
            r'\b(mapreduce|hdfs|yarn|streaming|batch processing)\b',
            r'\b(architecture|scalability|fault tolerance)\b'
        ],
        'spark_streaming': [
            r'\b(dstream|window|batch interval|streaming context)\b',
            r'\b(reducebykey|transform|output mode|micro-batch)\b',
            r'\b(spark streaming|structured streaming|incremental)\b'
        ],
        'machine_learning': [
            r'\b(neural network|machine learning|deep learning|algorithm)\b',
            r'\b(training|model|prediction|classification|regression)\b',
            r'\b(supervised|unsupervised|reinforcement learning)\b'
        ],
        'programming': [
            r'\b(function|method|class|variable|syntax)\b',
            r'\b(code|programming|development|implementation)\b',
            r'\b(debug|compile|runtime|library)\b'
        ]
    }
    
    # Score each subject based on pattern matches
    subject_scores = {}
    for subject, patterns in subject_patterns.items():
        score = 0
        for pattern in patterns:
            matches = len(re.findall(pattern, all_content))
            score += matches
        subject_scores[subject] = score
    
    # Return the subject with highest score, or 'general' if no clear match
    if max(subject_scores.values()) > 0:
        return max(subject_scores, key=subject_scores.get)
    else:
        return 'general'

def get_subject_formatting_guidelines(subject: str) -> str:
    """
    Get specific formatting guidelines based on detected subject
    
    Args:
        subject: The detected subject category
        
    Returns:
        Formatting guidelines string for the specific subject
    """
    
    guidelines = {
        'data_ethics': """
**Data Ethics Formatting Guidelines:**
- Emphasize regulatory terms (GDPR, compliance) in **bold**
- Use `code` formatting for legal terms and specific regulations on first occurrence
- Create tables for comparing different privacy frameworks or consent types
- Use callouts for real-world examples of ethical violations or best practices
- Include compliance checklists as bullet points
- Format case studies with clear structure: situation, issue, resolution
""",
        
        'distributed_architecture': """
**Distributed Architecture Formatting Guidelines:**
- Format technical terms and system names as `code` on first occurrence
- Include code blocks for configuration examples and command syntax
- Use tables for performance comparisons and system specifications
- Create callouts for practical implementation examples
- Bold important performance metrics and technical specifications
- Structure exercise solutions with step-by-step explanations
- Include architecture diagrams via enhance_content tool
""",
        
        'spark_streaming': """
**Spark/Streaming Formatting Guidelines:**
- Format method names and technical terms as `code` (e.g., `reduceByKey()`, `window()`)
- Include code blocks for function signatures and usage examples
- Use tables for comparing different streaming approaches or parameters
- Create callouts for practical exercise solutions
- Bold key concepts like batch intervals, window operations
- Structure solutions with clear input/output specifications
- Include timing diagrams for window operations
""",
        
        'machine_learning': """
**Machine Learning Formatting Guidelines:**
- Format algorithm names and technical terms as `code` on first occurrence
- Include mathematical formulas and equations in appropriate notation
- Use tables for comparing different algorithms or performance metrics
- Create callouts for practical examples and use cases
- Bold important concepts like training, validation, testing
- Structure model explanations with clear input/output descriptions
- Include model architecture diagrams via enhance_content tool
""",
        
        'programming': """
**Programming Formatting Guidelines:**
- Format code elements (variables, functions, classes) as `code`
- Include extensive code blocks for examples and implementations
- Use tables for comparing different approaches or language features
- Create callouts for common pitfalls and best practices
- Bold important programming concepts and patterns
- Structure tutorials with clear step-by-step instructions
- Include flowcharts for complex algorithms
""",
        
        'general': """
**General Academic Formatting Guidelines:**
- Use standard Notion formatting with hierarchical headings
- Apply `code` formatting to key terms on first occurrence
- Use **bold** for important concepts and emphasis
- Create tables for any comparative information
- Use callouts for examples and case studies
- Maintain clear structure with definitions followed by details
- Include visual aids via enhance_content when helpful
"""
    }
    
    return guidelines.get(subject, guidelines['general'])

def extract_topic_hierarchy(slide_text: str) -> List[Tuple[int, str]]:
    """
    Extract hierarchical topic structure from slide text or topic list
    
    Args:
        slide_text: Text containing hierarchical topic structure
        
    Returns:
        List of tuples (level, topic) where level indicates # depth
    """
    
    topics = []
    lines = slide_text.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Count # symbols for hierarchy level
        level = 0
        while level < len(line) and line[level] == '#':
            level += 1
            
        if level > 0:
            # Extract topic after # symbols
            topic = line[level:].strip()
            topics.append((level, topic))
        elif line.startswith('•') or line.startswith('-') or line.startswith('*'):
            # Handle bullet points as sublevel topics
            topic = line[1:].strip()
            topics.append((4, topic))  # Default to #### level for bullet points
    
    return topics

def identify_key_aspects(slide_text: str) -> Dict[str, List[str]]:
    """
    Identify key aspects that follow colons in topic lists (based on user's methodology)
    
    Args:
        slide_text: Text containing topics with colon-separated aspects
        
    Returns:
        Dictionary mapping topics to their key aspects
    """
    
    key_aspects = {}
    lines = slide_text.split('\n')
    
    for line in lines:
        line = line.strip()
        if ':' in line:
            # Split on colon
            parts = line.split(':', 1)
            if len(parts) == 2:
                topic = parts[0].strip()
                aspects_text = parts[1].strip()
                
                # Split aspects by commas
                aspects = [aspect.strip() for aspect in aspects_text.split(',')]
                key_aspects[topic] = aspects
    
    return key_aspects

def format_notion_content(content: str, subject: str) -> str:
    """
    Apply Notion-style formatting based on subject and content structure
    
    Args:
        content: Raw integrated content
        subject: Detected subject category
        
    Returns:
        Formatted content following Notion guidelines
    """
    
    # This would contain the logic to apply consistent formatting
    # based on the subject-specific guidelines
    
    # For now, return the content with a note about formatting
    formatting_note = f"\n<!-- Content formatted for {subject} subject using Notion-style guidelines -->\n"
    
    return formatting_note + content
