package com.elvarg.game.entity.impl.player.persistence.jsonfile;

import com.elvarg.Server;
import com.elvarg.game.entity.impl.player.Player;
import com.elvarg.game.entity.impl.player.persistence.PlayerPersistence;
import com.elvarg.game.entity.impl.player.persistence.PlayerSave;
import com.elvarg.util.Misc;
import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import com.password4j.Password;

import java.io.File;
import java.io.FileReader;
import java.io.FileWriter;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.logging.Level;

public class JSONFilePlayerPersistence extends PlayerPersistence {

    private static final String PATH = "./data/saves/characters/";
    private static final Gson BUILDER = new GsonBuilder().create();

    @Override
    public PlayerSave load(String username) {
        if (!exists(username)) {
            return null;
        }

        Path path = Paths.get(PATH, username + ".json");
        File file = path.toFile();

        try (FileReader fileReader = new FileReader(file)) {
            return BUILDER.fromJson(fileReader, PlayerSave.class);
        } catch (Exception e) {
            throw new RuntimeException(e);
        }
    }

    @Override
    public void save(Player player) {
        PlayerSave save = PlayerSave.fromPlayer(player);

        Path path = Paths.get(PATH, player.getUsername() + ".json");
        File file = path.toFile();
        setupDirectory(file);

        Gson builder = new GsonBuilder().setPrettyPrinting().create();

		try (FileWriter writer = new FileWriter(file)) {
			writer.write(builder.toJson(save));
		} catch (Exception e) {
			Server.getLogger().log(Level.SEVERE, "An error has occurred while saving a character file!", e);
            throw new RuntimeException(e);
		}
    }

    @Override
    public boolean exists(String username) {
        String formattedUsername = Misc.formatPlayerName(username.toLowerCase());
        return new File(PATH + formattedUsername + ".json").exists();
    }

    @Override
    public String encryptPassword(String plainPassword) {
        // Use Password4j BCrypt for secure password hashing
        try {
            return Password.hash(plainPassword).withBcrypt().getResult();
        } catch (Exception e) {
            Server.getLogger().log(Level.SEVERE, "Failed to encrypt password", e);
            // Fallback to plain text for compatibility, but log the issue
            Server.getLogger().log(Level.WARNING, "Using plain text password due to encryption failure - this is insecure!");
            return plainPassword;
        }
    }

    @Override
    public boolean checkPassword(String plainPassword, PlayerSave playerSave) {
        // Use Password4j to verify password
        try {
            String hashedPassword = playerSave.getPasswordHashWithSalt();
            // Check if password is already hashed (BCrypt format)
            if (hashedPassword.startsWith("$2a$") || hashedPassword.startsWith("$2b$") || hashedPassword.startsWith("$2y$")) {
                return Password.check(plainPassword, hashedPassword).withBcrypt();
            } else {
                // Legacy plain text password - compare directly but warn
                Server.getLogger().log(Level.WARNING, 
                    "Using plain text password comparison - consider updating to hashed password");
                return plainPassword.equals(hashedPassword);
            }
        } catch (Exception e) {
            Server.getLogger().log(Level.SEVERE, "Failed to check password", e);
            // Fallback to plain text comparison
            return plainPassword.equals(playerSave.getPasswordHashWithSalt());
        }
    }

    private void setupDirectory(File file) {
        file.getParentFile().setWritable(true);
        if (!file.getParentFile().exists()) {
            try {
                file.getParentFile().mkdirs();
            } catch (SecurityException e) {
                System.out.println("Unable to create directory for player data!");
                throw new RuntimeException(e);
            }
        }
    }
}
