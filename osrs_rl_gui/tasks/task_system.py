"""Task abstraction and natural language processing for OSRS RL Agent."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Any
import re
import logging

logger = logging.getLogger(__name__)


class TaskCategory(Enum):
    """Categories of OSRS tasks."""
    COMBAT = "combat"
    SKILLING = "skilling"
    QUESTING = "questing"
    TRADING = "trading"
    EXPLORATION = "exploration"
    PVP = "pvp"
    UNKNOWN = "unknown"


class TaskDifficulty(Enum):
    """Task difficulty levels."""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"  
    ADVANCED = "advanced"
    EXPERT = "expert"


@dataclass
class TaskRequirement:
    """Requirements for a task."""
    skill_levels: Dict[str, int]
    items: List[str]
    quests_completed: List[str]
    combat_level: Optional[int] = None


@dataclass
class TaskObjective:
    """A single objective within a task."""
    description: str
    target: str
    quantity: int = 1
    location: Optional[str] = None
    completed: bool = False


@dataclass
class Task:
    """Represents an OSRS task that can be learned and executed by the RL agent."""
    name: str
    description: str
    category: TaskCategory
    difficulty: TaskDifficulty
    objectives: List[TaskObjective]
    requirements: TaskRequirement
    estimated_duration: Optional[int] = None  # in minutes
    reward_xp: Dict[str, int] = None
    reward_items: List[str] = None
    
    def __post_init__(self):
        if self.reward_xp is None:
            self.reward_xp = {}
        if self.reward_items is None:
            self.reward_items = []


class TaskParser:
    """Natural language processor for converting plain English to Task objects."""
    
    def __init__(self):
        self._skill_keywords = {
            'attack', 'defence', 'strength', 'hitpoints', 'ranged', 'prayer',
            'magic', 'cooking', 'woodcutting', 'fletching', 'fishing', 'firemaking',
            'crafting', 'smithing', 'mining', 'herblore', 'agility', 'thieving',
            'slayer', 'farming', 'runecraft', 'hunter', 'construction'
        }
        
        self._combat_keywords = {
            'fight', 'kill', 'attack', 'combat', 'battle', 'pvp', 'pvm',
            'monster', 'boss', 'dragon', 'demon', 'giant', 'warrior'
        }
        
        self._skilling_keywords = {
            'mine', 'cut', 'fish', 'cook', 'craft', 'smith', 'make', 'create',
            'train', 'level', 'xp', 'experience', 'skill'
        }
        
        self._location_keywords = {
            'lumbridge', 'varrock', 'falador', 'camelot', 'ardougne', 'yanille',
            'draynor', 'edge', 'edgeville', 'wilderness', 'taverly', 'burthorpe'
        }
    
    def parse_task(self, description: str) -> Task:
        """Parse a natural language description into a Task object."""
        description = description.lower().strip()
        
        # Determine task category
        category = self._determine_category(description)
        
        # Extract objectives
        objectives = self._extract_objectives(description)
        
        # Determine difficulty based on keywords and complexity
        difficulty = self._determine_difficulty(description, objectives)
        
        # Extract requirements
        requirements = self._extract_requirements(description)
        
        # Generate task name
        name = self._generate_task_name(description)
        
        return Task(
            name=name,
            description=description,
            category=category,
            difficulty=difficulty,
            objectives=objectives,
            requirements=requirements
        )
    
    def _determine_category(self, description: str) -> TaskCategory:
        """Determine the task category from description."""
        words = set(description.split())
        
        if words.intersection(self._combat_keywords):
            return TaskCategory.COMBAT
        elif words.intersection(self._skilling_keywords):
            return TaskCategory.SKILLING
        elif 'quest' in description:
            return TaskCategory.QUESTING
        elif any(word in description for word in ['buy', 'sell', 'trade', 'exchange']):
            return TaskCategory.TRADING
        elif any(word in description for word in ['explore', 'find', 'locate', 'go to']):
            return TaskCategory.EXPLORATION
        elif 'pvp' in description or 'player' in description and 'kill' in description:
            return TaskCategory.PVP
        else:
            return TaskCategory.UNKNOWN
    
    def _extract_objectives(self, description: str) -> List[TaskObjective]:
        """Extract task objectives from description."""
        objectives = []
        
        # Look for quantity patterns like "kill 10 goblins"
        quantity_patterns = [
            r'(kill|mine|cut|cook|craft|make|get|obtain)\s+(\d+)\s+([a-z\s]+)',
            r'(\d+)\s+([a-z\s]+)\s+(killed|mined|cut|cooked|crafted|made)'
        ]
        
        for pattern in quantity_patterns:
            matches = re.findall(pattern, description)
            for match in matches:
                if len(match) == 3:
                    action, quantity, target = match
                    objectives.append(TaskObjective(
                        description=f"{action} {quantity} {target}".strip(),
                        target=target.strip(),
                        quantity=int(quantity)
                    ))
        
        # If no specific objectives found, create a general one
        if not objectives:
            objectives.append(TaskObjective(
                description=description,
                target="general",
                quantity=1
            ))
        
        return objectives
    
    def _determine_difficulty(self, description: str, objectives: List[TaskObjective]) -> TaskDifficulty:
        """Determine task difficulty."""
        # Simple heuristic based on keywords and complexity
        advanced_keywords = {'boss', 'raid', 'advanced', 'expert', 'high level', 'difficult'}
        intermediate_keywords = {'medium', 'moderate', 'some', 'several'}
        
        if any(keyword in description for keyword in advanced_keywords):
            return TaskDifficulty.ADVANCED
        elif any(keyword in description for keyword in intermediate_keywords):
            return TaskDifficulty.INTERMEDIATE
        elif len(objectives) > 3:
            return TaskDifficulty.INTERMEDIATE
        else:
            return TaskDifficulty.BEGINNER
    
    def _extract_requirements(self, description: str) -> TaskRequirement:
        """Extract task requirements from description."""
        skill_levels = {}
        items = []
        quests_completed = []
        
        # Look for skill level requirements
        level_pattern = r'(\d+)\s+([a-z]+)\s+(?:level|skill)'
        level_matches = re.findall(level_pattern, description)
        for level, skill in level_matches:
            if skill in self._skill_keywords:
                skill_levels[skill] = int(level)
        
        # Look for item requirements
        item_pattern = r'(?:need|require|bring|have)\s+([a-z\s]+?)(?:\s+(?:and|or|,)|$)'
        item_matches = re.findall(item_pattern, description)
        for item_match in item_matches:
            items.append(item_match.strip())
        
        return TaskRequirement(
            skill_levels=skill_levels,
            items=items,
            quests_completed=quests_completed
        )
    
    def _generate_task_name(self, description: str) -> str:
        """Generate a concise task name from description."""
        # Take first few words and capitalize
        words = description.split()[:5]
        return ' '.join(word.capitalize() for word in words)


class TaskManager:
    """Manages tasks for the OSRS RL Agent."""
    
    def __init__(self):
        self.tasks: List[Task] = []
        self.parser = TaskParser()
    
    def create_task_from_description(self, description: str) -> Task:
        """Create a new task from natural language description."""
        task = self.parser.parse_task(description)
        self.tasks.append(task)
        logger.info(f"Created task: {task.name}")
        return task
    
    def get_tasks_by_category(self, category: TaskCategory) -> List[Task]:
        """Get all tasks in a specific category."""
        return [task for task in self.tasks if task.category == category]
    
    def get_tasks_by_difficulty(self, difficulty: TaskDifficulty) -> List[Task]:
        """Get all tasks of a specific difficulty."""
        return [task for task in self.tasks if task.difficulty == difficulty]
    
    def mark_objective_complete(self, task: Task, objective_index: int) -> None:
        """Mark a task objective as completed."""
        if 0 <= objective_index < len(task.objectives):
            task.objectives[objective_index].completed = True
            logger.info(f"Marked objective {objective_index} complete for task {task.name}")
    
    def is_task_complete(self, task: Task) -> bool:
        """Check if all task objectives are completed."""
        return all(obj.completed for obj in task.objectives)
    
    def get_incomplete_tasks(self) -> List[Task]:
        """Get all tasks that are not yet completed."""
        return [task for task in self.tasks if not self.is_task_complete(task)]