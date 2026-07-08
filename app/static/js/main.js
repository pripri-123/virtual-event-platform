/**
 * Virtual Event Hosting Platform — Main JavaScript
 * Phase 3: minimal bootstrap; dark mode and charts added in later phases.
 */

document.addEventListener("DOMContentLoaded", () => {
    // Auto-dismiss flash alerts after 5 seconds
    document.querySelectorAll(".alert-dismissible").forEach((alert) => {
        setTimeout(() => {
            const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
            bsAlert.close();
        }, 5000);
    });

    console.log("VEHP — Phase 3 structure loaded.");
});
