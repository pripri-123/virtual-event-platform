/**
 * Render Chart.js charts from data embedded in the page.
 * Expects window.VEHP_CHARTS = [{ id, type, labels, datasets, options? }, ...]
 */
(function () {
    "use strict";

    if (typeof Chart === "undefined" || !window.VEHP_CHARTS) {
        return;
    }

    const palette = [
        "#0d6efd", "#198754", "#ffc107", "#dc3545",
        "#6f42c1", "#0dcaf0", "#fd7e14", "#20c997",
    ];

    window.VEHP_CHARTS.forEach(function (spec, index) {
        const canvas = document.getElementById(spec.id);
        if (!canvas) {
            return;
        }

        const datasets = (spec.datasets || []).map(function (ds, dsIndex) {
            const color = palette[(index + dsIndex) % palette.length];
            return Object.assign(
                {
                    backgroundColor: spec.type === "line"
                        ? color + "33"
                        : palette.slice(0, spec.labels.length),
                    borderColor: color,
                    borderWidth: spec.type === "line" ? 2 : 1,
                    tension: 0.3,
                    fill: spec.type === "line",
                },
                ds
            );
        });

        new Chart(canvas, {
            type: spec.type,
            data: { labels: spec.labels, datasets: datasets },
            options: Object.assign(
                {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { position: "bottom" } },
                },
                spec.options || {}
            ),
        });
    });
})();
