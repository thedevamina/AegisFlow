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
    Schema::create('pull_requests', function (Blueprint $table) {
        $table->id();
        $table->foreignId('repo_id')->constrained('repos')->cascadeOnDelete();
        $table->integer('github_pr_number');
        $table->string('title');
        $table->string('author_login');
        $table->integer('author_pr_count')->default(0);
        $table->string('state');
        $table->timestamp('created_at_github')->nullable();
        $table->timestamp('merged_at_github')->nullable();
        $table->timestamp('closed_at_github')->nullable();
        $table->integer('additions')->default(0);
        $table->integer('deletions')->default(0);
        $table->integer('changed_files_count')->default(0);
        $table->boolean('test_files_touched')->default(false);
        $table->jsonb('raw_payload')->nullable();
        $table->timestamps();
        $table->unique(['repo_id', 'github_pr_number']);
    });
}

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::dropIfExists('pull_requests');
    }
};
