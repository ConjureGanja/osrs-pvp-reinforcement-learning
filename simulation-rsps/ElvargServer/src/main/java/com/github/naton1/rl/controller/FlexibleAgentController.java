/**
 * Enhanced agent controller for flexible OSRS task execution.
 * Replaces complex state machines with maintainable task-based approach.
 */
package com.github.naton1.rl.controller;

import com.elvarg.game.entity.impl.player.Player;
import com.github.naton1.rl.env.AgentEnvironment;
import lombok.extern.slf4j.Slf4j;

import java.util.concurrent.CompletableFuture;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.function.Consumer;

/**
 * Flexible agent controller that can handle various OSRS tasks beyond just PvP.
 * Replaces the complex state machine with a more maintainable task-based approach.
 */
@Slf4j
public class FlexibleAgentController {
    
    private final Player agent;
    private final AgentEnvironment environment;
    private final Map<String, TaskHandler> taskHandlers = new ConcurrentHashMap<>();
    
    private volatile boolean isActive = false;
    private volatile String currentTaskType = "idle";
    private volatile CompletableFuture<Void> currentTask;
    
    public FlexibleAgentController(Player agent, AgentEnvironment environment) {
        this.agent = agent;
        this.environment = environment;
        initializeDefaultHandlers();
    }
    
    private void initializeDefaultHandlers() {
        // Register default task handlers
        registerTaskHandler("combat", new CombatTaskHandler());
        registerTaskHandler("skilling", new SkillingTaskHandler());
        registerTaskHandler("exploration", new ExplorationTaskHandler());
        registerTaskHandler("idle", new IdleTaskHandler());
    }
    
    public void registerTaskHandler(String taskType, TaskHandler handler) {
        taskHandlers.put(taskType, handler);
        log.info("Registered task handler for: {}", taskType);
    }
    
    public CompletableFuture<Void> executeTask(String taskType, Map<String, Object> parameters) {
        if (currentTask != null && !currentTask.isDone()) {
            log.warn("Interrupting current task to start new task: {}", taskType);
            currentTask.cancel(true);
        }
        
        TaskHandler handler = taskHandlers.get(taskType);
        if (handler == null) {
            log.error("No handler found for task type: {}", taskType);
            return CompletableFuture.failedFuture(
                new IllegalArgumentException("Unknown task type: " + taskType)
            );
        }
        
        currentTaskType = taskType;
        isActive = true;
        
        TaskContext context = new TaskContext(agent, environment, parameters);
        currentTask = CompletableFuture.runAsync(() -> {
            try {
                handler.executeTask(context);
                log.info("Task completed successfully: {}", taskType);
            } catch (Exception e) {
                log.error("Task execution failed: {}", taskType, e);
                throw new RuntimeException("Task execution failed", e);
            } finally {
                isActive = false;
                currentTaskType = "idle";
            }
        });
        
        return currentTask;
    }
    
    public void stop() {
        isActive = false;
        if (currentTask != null && !currentTask.isDone()) {
            currentTask.cancel(true);
        }
        log.info("Agent controller stopped");
    }
    
    public boolean isActive() {
        return isActive;
    }
    
    public String getCurrentTaskType() {
        return currentTaskType;
    }
    
    // Task context for handlers
    public static class TaskContext {
        private final Player agent;
        private final AgentEnvironment environment;
        private final Map<String, Object> parameters;
        
        public TaskContext(Player agent, AgentEnvironment environment, Map<String, Object> parameters) {
            this.agent = agent;
            this.environment = environment;
            this.parameters = parameters;
        }
        
        public Player getAgent() { return agent; }
        public AgentEnvironment getEnvironment() { return environment; }
        public Map<String, Object> getParameters() { return parameters; }
        
        @SuppressWarnings("unchecked")
        public <T> T getParameter(String key, T defaultValue) {
            return (T) parameters.getOrDefault(key, defaultValue);
        }
    }
    
    // Base interface for task handlers
    public interface TaskHandler {
        void executeTask(TaskContext context) throws Exception;
    }
    
    // Default task handlers
    private static class CombatTaskHandler implements TaskHandler {
        @Override
        public void executeTask(TaskContext context) throws Exception {
            log.info("Executing combat task for agent: {}", context.getAgent().getUsername());
            // Implementation would handle combat-specific logic
            // This replaces the complex PvP-only state machine with flexible task handling
        }
    }
    
    private static class SkillingTaskHandler implements TaskHandler {
        @Override
        public void executeTask(TaskContext context) throws Exception {
            log.info("Executing skilling task for agent: {}", context.getAgent().getUsername());
            // Implementation would handle skilling tasks like mining, woodcutting, etc.
        }
    }
    
    private static class ExplorationTaskHandler implements TaskHandler {
        @Override
        public void executeTask(TaskContext context) throws Exception {
            log.info("Executing exploration task for agent: {}", context.getAgent().getUsername());
            // Implementation would handle movement and exploration tasks
        }
    }
    
    private static class IdleTaskHandler implements TaskHandler {
        @Override
        public void executeTask(TaskContext context) throws Exception {
            log.debug("Agent idle: {}", context.getAgent().getUsername());
            // Minimal processing for idle state
        }
    }
}