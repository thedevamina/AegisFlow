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
    Schema::create('predictions', function (Blueprint $table) {
        $table->id();
        $table->foreignId('pull_request_id')->constrained('pull_requests')->cascadeOnDelete();
        $table->string('model_version');
        $table->float('risk_score');
        $table->boolean('risk_label');
        $table->text('summary')->nullable();
        $table->timestamp('predicted_at')->nullable();
        $table->timestamps();
    });
}

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::dropIfExists('predictions');
    }
};
