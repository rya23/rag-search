"use client";

import { TraceDetail } from "@/lib/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { BarChart, Bar, Cell, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Legend } from "recharts";
import { Zap, TrendingUp, Clock } from "lucide-react";

interface TracePerformanceProps {
  trace: TraceDetail;
}

export function TracePerformance({ trace }: TracePerformanceProps) {
  if (trace.retriever_ms === undefined && trace.generator_ms === undefined && trace.total_ms === undefined) {
    return (
      <Card className="card-elevated">
        <CardContent className="py-12 text-center">
          <div className="inline-flex h-16 w-16 items-center justify-center rounded-2xl bg-muted mb-4">
            <TrendingUp className="w-8 h-8 text-muted-foreground" />
          </div>
          <h3 className="text-lg font-semibold text-display mb-2">No Performance Data</h3>
          <p className="text-sm text-muted-foreground">
            Performance metrics are not available for this trace.
          </p>
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

  // Prepare data for pie chart with distinct colors
  const pieData = [
    {
      name: "Retrieval",
      value: trace.retriever_ms || 0,
      fill: "hsl(var(--chart-1))",
    },
    {
      name: "Generation",
      value: trace.generator_ms || 0,
      fill: "hsl(var(--chart-2))",
    },
  ].filter((item) => item.value > 0);

  const totalTime = trace.total_ms || (trace.retriever_ms || 0) + (trace.generator_ms || 0);

  return (
    <div className="space-y-4 animate-in">
      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="card-elevated">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
              <div className="h-2 w-2 rounded-full bg-chart-1" />
              Retrieval Time
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-baseline gap-2">
              <span className="text-3xl font-bold font-mono">
                {trace.retriever_ms || 0}
              </span>
              <span className="text-sm text-muted-foreground">ms</span>
            </div>
            {totalTime > 0 && (
              <p className="text-xs text-muted-foreground mt-2">
                {((((trace.retriever_ms || 0) / totalTime) * 100).toFixed(1))}% of total
              </p>
            )}
          </CardContent>
        </Card>

        <Card className="card-elevated">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
              <div className="h-2 w-2 rounded-full bg-chart-2" />
              Generation Time
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-baseline gap-2">
              <span className="text-3xl font-bold font-mono">
                {trace.generator_ms || 0}
              </span>
              <span className="text-sm text-muted-foreground">ms</span>
            </div>
            {totalTime > 0 && (
              <p className="text-xs text-muted-foreground mt-2">
                {((((trace.generator_ms || 0) / totalTime) * 100).toFixed(1))}% of total
              </p>
            )}
          </CardContent>
        </Card>

        <Card className="card-elevated border-chart-1/30 bg-chart-1/5">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <Zap className="h-4 w-4 text-chart-1" />
              Total Time
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-baseline gap-2">
              <span className="text-3xl font-bold font-mono text-chart-1">
                {totalTime}
              </span>
              <span className="text-sm text-muted-foreground">ms</span>
            </div>
            <p className="text-xs text-muted-foreground mt-2">
              End-to-end query latency
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Bar Chart */}
        <Card className="card-elevated">
          <CardHeader>
            <CardTitle className="text-base text-display">Time Breakdown</CardTitle>
            <p className="text-xs text-muted-foreground">Milliseconds by stage</p>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={barData}>
                <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                <XAxis 
                  dataKey="name" 
                  className="text-xs"
                  tick={{ fill: 'hsl(var(--foreground))' }}
                />
                <YAxis 
                  className="text-xs"
                  tick={{ fill: 'hsl(var(--foreground))' }}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "hsl(var(--popover))",
                    border: "1px solid hsl(var(--border))",
                    borderRadius: "var(--radius)",
                    color: "hsl(var(--popover-foreground))",
                  }}
                  labelStyle={{ color: "hsl(var(--popover-foreground))" }}
                  itemStyle={{ color: "hsl(var(--popover-foreground))" }}
                  formatter={(value) => [`${value}ms`, "Time"]}
                />
                <Bar dataKey="time" radius={[8, 8, 0, 0]}>
                  <Cell fill="hsl(var(--chart-1))" />
                  <Cell fill="hsl(var(--chart-2))" />
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

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
                  stroke="hsl(var(--background))"
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
                    paddingTop: '20px',
                    color: 'hsl(var(--foreground))'
                  }}
                  iconType="circle"
                />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Performance Insights */}
      <Card className="card-elevated">
        <CardHeader>
          <CardTitle className="text-base text-display flex items-center gap-2">
            <TrendingUp className="h-5 w-5 text-chart-1" />
            Performance Insights
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {trace.retriever_ms && trace.generator_ms && (
              <div className="flex items-start gap-3 text-sm">
                <Clock className="h-4 w-4 text-muted-foreground mt-0.5 shrink-0" />
                <div>
                  <p className="font-medium">
                    {trace.retriever_ms > trace.generator_ms
                      ? "Retrieval is the bottleneck"
                      : "Generation is the bottleneck"}
                  </p>
                  <p className="text-xs text-muted-foreground mt-1">
                    {trace.retriever_ms > trace.generator_ms
                      ? "Consider optimizing vector search or reducing the k parameter."
                      : "LLM generation took longer. Consider using a faster model for simple queries."}
                  </p>
                </div>
              </div>
            )}
            
            {totalTime < 1000 && (
              <div className="flex items-start gap-3 text-sm">
                <Zap className="h-4 w-4 text-chart-1 mt-0.5 shrink-0" />
                <div>
                  <p className="font-medium text-chart-1">Excellent performance!</p>
                  <p className="text-xs text-muted-foreground mt-1">
                    Query completed in under 1 second with great user experience.
                  </p>
                </div>
              </div>
            )}

            {totalTime >= 1000 && totalTime < 3000 && (
              <div className="flex items-start gap-3 text-sm">
                <TrendingUp className="h-4 w-4 text-chart-3 mt-0.5 shrink-0" />
                <div>
                  <p className="font-medium">Good performance</p>
                  <p className="text-xs text-muted-foreground mt-1">
                    Query completed in reasonable time. Consider caching for frequently asked questions.
                  </p>
                </div>
              </div>
            )}

            {totalTime >= 3000 && (
              <div className="flex items-start gap-3 text-sm">
                <Clock className="h-4 w-4 text-destructive mt-0.5 shrink-0" />
                <div>
                  <p className="font-medium text-destructive">Slow query detected</p>
                  <p className="text-xs text-muted-foreground mt-1">
                    Query took over 3 seconds. Review retrieval strategy and consider optimization.
                  </p>
                </div>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
