"use client";

import Image from "next/image";
import { CopilotSidebar } from "@copilotkit/react-ui";
import { useRenderToolCall } from "@copilotkit/react-core";

export default function Page() {
  useRenderToolCall({
    name: "check_gcp_service_availability",
    render: ({ status, args }) => {
      return (
        <p className="text-gray-500 mt-2">
          {status !== "complete" && "Calling availability API..."}
          {status === "complete" &&
            `Called the availability API for ${args.service_name}.`}
        </p>
      );
    },
  });

  const services = [
    { name: "Compute Engine", icon: "🖥️", status: "Active", usage: "78%" },
    { name: "Cloud Storage", icon: "💾", status: "Active", usage: "62%" },
    { name: "BigQuery", icon: "📊", status: "Active", usage: "45%" },
    { name: "Cloud Run", icon: "🚀", status: "Active", usage: "34%" },
    { name: "Kubernetes Engine", icon: "⎈", status: "Active", usage: "56%" },
    { name: "Cloud Functions", icon: "⚡", status: "Active", usage: "29%" },
  ];

  const recentUpdates = [
    { date: "Feb 1, 2026", title: "New BigQuery cost optimization guidelines released", type: "Documentation" },
    { date: "Jan 28, 2026", title: "Q1 Cloud Architecture Review scheduled", type: "Event" },
    { date: "Jan 25, 2026", title: "Security best practices workshop completed", type: "Training" },
    { date: "Jan 22, 2026", title: "New service account templates available", type: "Resource" },
  ];

  const quickLinks = [
    { name: "Architecture Patterns", desc: "Reference architectures and design patterns" },
    { name: "Cost Management", desc: "Budgets, optimization, and reporting tools" },
    { name: "Security & Compliance", desc: "Policies, standards, and audit guidelines" },
    { name: "Training & Certification", desc: "Learning paths and certification programs" },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-gray-100">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-blue-600 rounded-lg flex items-center justify-center">
                <span className="text-white text-xl font-bold">☁️</span>
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">Google Cloud CoE</h1>
                <p className="text-sm text-gray-600">Center of Excellence Portal</p>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-600">Enterprise Solutions</span>
              <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                <span className="text-blue-600 font-semibold text-sm">JD</span>
              </div>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-8">
        {/* Stats Overview */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="text-3xl font-bold text-blue-600">127</div>
            <div className="text-sm text-gray-600 mt-1">Active Projects</div>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <div className="text-3xl font-bold text-green-600">$2.4M</div>
            <div className="text-sm text-gray-600 mt-1">Monthly Spend</div>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <div className="text-3xl font-bold text-purple-600">342</div>
            <div className="text-sm text-gray-600 mt-1">Team Members</div>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <div className="text-3xl font-bold text-orange-600">98.7%</div>
            <div className="text-sm text-gray-600 mt-1">Uptime SLA</div>
          </div>
        </div>

        {/* Quick Links */}
        <div className="mb-8">
          <h2 className="text-xl font-bold text-gray-900 mb-4">Quick Access</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {quickLinks.map((link, idx) => (
              <div key={idx} className="bg-white rounded-lg shadow p-5 hover:shadow-lg transition-shadow cursor-pointer border border-gray-100">
                <h3 className="font-semibold text-gray-900 mb-2">{link.name}</h3>
                <p className="text-sm text-gray-600">{link.desc}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Services Grid */}
        <div className="mb-8">
          <h2 className="text-xl font-bold text-gray-900 mb-4">Active GCP Services</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {services.map((service, idx) => (
              <div key={idx} className="bg-white rounded-lg shadow p-5 border border-gray-100">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center space-x-3">
                    <span className="text-2xl">{service.icon}</span>
                    <h3 className="font-semibold text-gray-900">{service.name}</h3>
                  </div>
                  <span className="px-2 py-1 bg-green-100 text-green-700 text-xs font-medium rounded">
                    {service.status}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Usage</span>
                  <span className="text-sm font-semibold text-blue-600">{service.usage}</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
                  <div 
                    className="bg-blue-600 h-2 rounded-full" 
                    style={{ width: service.usage }}
                  ></div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Recent Updates */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4">Recent Updates</h2>
          <div className="space-y-4">
            {recentUpdates.map((update, idx) => (
              <div key={idx} className="flex items-start space-x-4 pb-4 border-b border-gray-100 last:border-0">
                <div className="flex-shrink-0">
                  <div className="w-12 h-12 bg-blue-50 rounded-lg flex items-center justify-center">
                    <span className="text-blue-600 font-semibold text-xs">{update.type.slice(0, 3)}</span>
                  </div>
                </div>
                <div className="flex-1">
                  <h3 className="font-medium text-gray-900">{update.title}</h3>
                  <div className="flex items-center space-x-3 mt-1">
                    <span className="text-sm text-gray-500">{update.date}</span>
                    <span className="px-2 py-0.5 bg-gray-100 text-gray-700 text-xs rounded">{update.type}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </main>

      <CopilotSidebar />
    </div>
  );
}
