"use client";

import { TraceDetail } from "@/lib/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { BarChart, Bar, Cell, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Legend } from "recharts";
import { Zap, TrendingUp, Clock } from "lucide-react";

interface TracePerformanceProps {
    trace: TraceDetail;
}

interface ColorConfig {
    fill: string;
    light: string;
    dark: string;
}

const chartColors: { [key: string]: ColorConfig } = {
    retrieval: {
        fill: "#6b7280",
        light: "bg-gray-500",
        dark: "bg-gray-600",
    },
    generation: {
        fill: "#d1d5db",
        light: "bg-gray-300",
        dark: "bg-gray-400",
    },
};

export function TracePerformance({ trace }: TracePerformanceProps) {
    if (trace.retriever_ms === undefined && trace.generator_ms === undefined && trace.total_ms === undefined) {
        return (
            <Card className="card-elevated">
                <CardContent className="py-12 text-center">
                    <div className="inline-flex h-16 w-16 items-center justify-center rounded-2xl bg-muted mb-4">
                        <TrendingUp className="w-8 h-8 text-muted-foreground" />
                    </div>
                    <h3 className="text-lg font-semibold text-display mb-2">No Performance Data</h3>
                    <p className="text-sm text-muted-foreground">Performance metrics are not available for this trace.</p>
                </CardContent>
            </Card>
        );
    }

    // Prepare data for bar chart
    const barData = [
        {
            name: "Retrieval",
            time: trace.retriever_ms || 0,
        },
        {
            name: "Generation",
            time: trace.generator_ms || 0,
        },
    ].filter((item) => item.time > 0);

    // Prepare data for pie chart with distinct shadcn colors
    const pieData = [
        {
            name: "Retrieval",
            value: trace.retriever_ms || 0,
            fill: chartColors.retrieval.fill,
        },
        {
            name: "Generation",
            value: trace.generator_ms || 0,
            fill: chartColors.generation.fill,
        },
    ].filter((item) => item.value > 0);

    const totalTime = trace.total_ms || (trace.retriever_ms || 0) + (trace.generator_ms || 0);

    return (
        <div className="space-y-4 animate-in">
            {/* Summary Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <Card className="card-elevated border-l-4" style={{ borderLeftColor: chartColors.retrieval.fill }}>
                    <CardHeader className="pb-3">
                        <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
                            <div className="h-3 w-3 rounded-full" style={{ backgroundColor: chartColors.retrieval.fill }} />
                            Retrieval Time
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="flex items-baseline gap-2">
                            <span className="text-3xl font-bold font-mono">{trace.retriever_ms || 0}</span>
                            <span className="text-sm text-muted-foreground">ms</span>
                        </div>
                        {totalTime > 0 && (
                            <p className="text-xs text-muted-foreground mt-2">
                                {(((trace.retriever_ms || 0) / totalTime) * 100).toFixed(1)}% of total
                            </p>
                        )}
                    </CardContent>
                </Card>

                <Card className="card-elevated border-l-4" style={{ borderLeftColor: chartColors.generation.fill }}>
                    <CardHeader className="pb-3">
                        <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
                            <div className="h-3 w-3 rounded-full" style={{ backgroundColor: chartColors.generation.fill }} />
                            Generation Time
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="flex items-baseline gap-2">
                            <span className="text-3xl font-bold font-mono">{trace.generator_ms || 0}</span>
                            <span className="text-sm text-muted-foreground">ms</span>
                        </div>
                        {totalTime > 0 && (
                            <p className="text-xs text-muted-foreground mt-2">
                                {(((trace.generator_ms || 0) / totalTime) * 100).toFixed(1)}% of total
                            </p>
                        )}
                    </CardContent>
                </Card>

                <Card className="card-elevated border-l-4" style={{ borderLeftColor: "#4b5563" }}>
                    <CardHeader className="pb-3">
                        <CardTitle className="text-sm font-medium flex items-center gap-2" style={{ color: "#4b5563" }}>
                            <Zap className="h-4 w-4" />
                            Total Time
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="flex items-baseline gap-2">
                            <span className="text-3xl font-bold font-mono" style={{ color: "#4b5563" }}>
                                {totalTime}
                            </span>

                            <span className="text-sm text-muted-foreground">ms</span>
                        </div>
                        <p className="text-xs text-muted-foreground mt-2">End-to-end query latency</p>
                    </CardContent>
                </Card>
            </div>

            {/* Charts */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                {/* Bar Chart */}

                {/* Pie Chart */}
                <Card className="card-elevated">
                    <CardHeader>
                        <CardTitle className="text-base text-display">Time Distribution</CardTitle>
                        <p className="text-xs text-muted-foreground">Percentage by stage</p>
                    </CardHeader>
                    <CardContent>
                        <ResponsiveContainer width="100%" height={250}>
                            <PieChart>
                                <Pie
                                    data={pieData}
                                    cx="50%"
                                    cy="50%"
                                    labelLine={false}
                                    label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                                    outerRadius={80}
                                    dataKey="value"
                                    stroke="white"
                                    strokeWidth={2}
                                >
                                    {pieData.map((entry, index) => (
                                        <Cell key={`cell-${index}`} fill={entry.fill} />
                                    ))}
                                </Pie>
                                <Tooltip
                                    contentStyle={{
                                        backgroundColor: "hsl(var(--popover))",
                                        border: "1px solid hsl(var(--border))",
                                        borderRadius: "var(--radius)",
                                        color: "hsl(var(--popover-foreground))",
                                    }}
                                    itemStyle={{ color: "hsl(var(--popover-foreground))" }}
                                    formatter={(value) => [`${value}ms`, "Time"]}
                                />
                                <Legend
                                    wrapperStyle={{
                                        paddingTop: "20px",
                                        color: "hsl(var(--foreground))",
                                    }}
                                    iconType="circle"
                                />
                            </PieChart>
                        </ResponsiveContainer>
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}
