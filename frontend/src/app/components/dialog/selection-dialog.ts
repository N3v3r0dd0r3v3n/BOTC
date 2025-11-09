import { Component, Inject } from '@angular/core';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material/dialog';
import { MatDialogModule } from '@angular/material/dialog';
import { MatButtonModule } from '@angular/material/button';
import { CommonModule } from '@angular/common';
import { MatSelectModule } from '@angular/material/select';
import { MatRadioModule } from '@angular/material/radio';
import { FormsModule } from '@angular/forms';
import { Option } from '../../models/message.model';

@Component({
  selector: 'app-yes-no-dialog',
  imports: [
    CommonModule,
    MatDialogModule,
    MatButtonModule,
    MatRadioModule,
    FormsModule
  ],
    
  templateUrl: './selection-dialog.html',
  styleUrl: './selection-dialog.css'
})
export class Dialog {

  selection?: Option

  constructor(
    public dialogRef: MatDialogRef<Dialog>,
    @Inject(MAT_DIALOG_DATA) public data: { 
      title: string
      options: Option[]}
  ) {}

  onConfirm(): void {
    this.dialogRef.close(this.selection!);
  }

  isDisabled(): boolean {
    return this.selection == undefined
  }
}
