/** @odoo-module **/

import { Component } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";

const DAY = 24 * 3600 * 1000;

/**
 * Progress over time: actual progress at each check-in against the expected
 * pace (a straight line from 0% at the start to 100% at the end of the cycle).
 * Inspired by the burn-up charts of Viva Goals / Perdoo.
 */
export class OkrProgressChart extends Component {
    static template = "okr_scale.ProgressChart";
    static props = { ...standardFieldProps };

    width = 1200;
    height = 260;
    pad = { left: 36, right: 16, top: 16, bottom: 28 };

    get data() {
        return this.props.record.data[this.props.name];
    }

    parse(day) {
        return new Date(day + "T00:00:00").getTime();
    }

    get chart() {
        const data = this.data;
        if (!data || !data.points || !data.points.length) {
            return null;
        }
        const start = this.parse(data.start);
        const end = Math.max(this.parse(data.end), start + DAY);
        const today = this.parse(data.today);
        const { left, right, top, bottom } = this.pad;
        const w = this.width - left - right;
        const h = this.height - top - bottom;
        const x = (t) => left + Math.max(0, Math.min(1, (t - start) / (end - start))) * w;
        const y = (v) => top + (1 - Math.max(0, Math.min(100, v)) / 100) * h;
        const points = data.points.map(([day, value]) => ({ x: x(this.parse(day)), y: y(value), value, day }));
        const line = points.map((p, i) => `${i ? "L" : "M"}${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(" ");
        const last = points[points.length - 1];
        const area = `${line} L${last.x.toFixed(1)},${y(0)} L${points[0].x.toFixed(1)},${y(0)} Z`;
        const expectedNow = Math.max(0, Math.min(100, ((today - start) / (end - start)) * 100));
        const gap = Math.round(last.value - expectedNow);
        const months = [];
        const cursor = new Date(start);
        cursor.setDate(1);
        while (cursor.getTime() <= end) {
            if (cursor.getTime() >= start) {
                months.push({ x: x(cursor.getTime()), label: `${cursor.getMonth() + 1}/${cursor.getFullYear() % 100}` });
            }
            cursor.setMonth(cursor.getMonth() + 1);
        }
        return {
            line,
            area,
            points,
            last,
            expected: { x1: x(start), y1: y(0), x2: x(end), y2: y(100) },
            today: { x: x(today), visible: today >= start && today <= end },
            grid: [0, 25, 50, 75, 100].map((v) => ({ y: y(v), label: `${v}%` })),
            months,
            expectedNow: Math.round(expectedNow),
            gap,
            ahead: gap >= 0,
        };
    }
}

registry.category("fields").add("okr_progress_chart", {
    component: OkrProgressChart,
    supportedTypes: ["json"],
});
