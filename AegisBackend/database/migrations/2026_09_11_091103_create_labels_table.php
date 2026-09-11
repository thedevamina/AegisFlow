<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    /**
     * Run the migrations.
     */
  public function up(): void
{
    Schema::create('labels', function (Blueprint $table) {
        $table->id();
        $table->foreignId('pull_request_id')->constrained('pull_requests')->cascadeOnDelete()->unique();
        $table->boolean('is_risky')->default(false);
        $table->string('risk_reason')->nullable();
        $table->timestamp('evaluated_at')->nullable();
        $table->timestamps();
    });
}

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::dropIfExists('labels');
    }
};
