class NotesController < ApplicationController
  def create
    body = save_note
    logger.info("sent #{body.length} bytes")
  end

  private

  def save_note
    render plain: "saved"
  end
end
